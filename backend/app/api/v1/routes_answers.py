from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import asyncio
import logging
import json
from ...core.database import get_db, async_session_maker
from ...models.answer import Answer
from ...models.analysis import AnalysisResult
from ...models.question import Question
from ...schemas.answer import (
    AnswerCreate,
    AnswerResponse,
    AnswerWithAnalysis,
    AnalysisResultResponse,
    HistoryAnalyzeRequest,
    PaperAnalyzeRequest
)
from ...services.analyze_service import AnalyzeService
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/answers", tags=["作答管理"])

# 分析锁（简单实现）
analysis_locks: dict[int, bool] = {}


@router.post("", response_model=AnswerResponse)
async def create_answer(
    data: AnswerCreate,
    db: AsyncSession = Depends(get_db)
):
    """提交作答"""
    # 验证 mode
    if data.mode not in ("single", "paper"):
        raise HTTPException(status_code=400, detail="mode 必须为 single 或 paper")

    # 验证 question_id 存在性
    result = await db.execute(select(Question).where(Question.id == data.question_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="题目不存在")

    # 验证 paper 模式业务规则
    if data.mode == "paper":
        if not data.paper_session_id:
            raise HTTPException(status_code=400, detail="套卷模式需要 paper_session_id")
    elif data.paper_id or data.paper_session_id:
        raise HTTPException(status_code=400, detail="单题模式不能传入 paper_id 或 paper_session_id")

    answer = Answer(
        mode=data.mode,
        question_id=data.question_id,
        paper_id=data.paper_id,
        paper_session_id=data.paper_session_id,
        transcript=data.transcript,
        audio_url=data.audio_url,
        duration_seconds=data.duration_seconds,
        started_at=data.started_at,
        finished_at=data.finished_at,
        practice_date=data.started_at.strftime("%Y-%m-%d")
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return AnswerResponse.model_validate(answer)


@router.get("/{answer_id}", response_model=AnswerWithAnalysis)
async def get_answer(
    answer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取作答详情"""
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.analysis), selectinload(Answer.question))
        .where(Answer.id == answer_id)
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="作答记录不存在")

    response = AnswerWithAnalysis.model_validate(answer)
    response.question_content = answer.question.content if answer.question else None
    return response


async def run_analysis(answer_id: int):
    """后台分析任务 - 使用独立的数据库会话"""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(Answer)
                .options(selectinload(Answer.question))
                .where(Answer.id == answer_id)
            )
            answer = result.scalar_one_or_none()
            if not answer:
                logger.warning(f"分析任务: 作答记录 {answer_id} 不存在")
                return

            service = AnalyzeService(db)
            analysis_result = await service.analyze_answer(
                question=answer.question.content,
                answer=answer.transcript or "",
                duration=answer.duration_seconds or 0,
                prompt_type="single_analyze"
            )

            # 从反馈中提取分数
            score = None
            feedback = analysis_result["feedback"]
            score_match = re.search(r"总体评分[：:]\s*(\d+(?:\.\d+)?)", feedback)
            if score_match:
                score = float(score_match.group(1))

            # 保存分析结果
            analysis = AnalysisResult(
                answer_id=answer_id,
                analysis_type="single",
                score=score,
                feedback=feedback,
                model_name=analysis_result["model_name"]
            )
            db.add(analysis)
            await db.commit()
            logger.info(f"分析任务完成: answer_id={answer_id}, score={score}")
        except Exception as e:
            logger.error(f"分析任务失败: answer_id={answer_id}, error={e}")


@router.post("/{answer_id}/analyze")
async def analyze_answer(
    answer_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """触发 AI 分析（单题）"""
    result = await db.execute(
        select(Answer).where(Answer.id == answer_id)
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="作答记录不存在")

    # 检查是否已有分析结果
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.answer_id == answer_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已有分析结果")

    # 后台执行分析（不再传入 db 会话）
    background_tasks.add_task(run_analysis, answer_id)

    return {"message": "分析任务已提交", "answer_id": answer_id}


@router.get("/{answer_id}/analysis", response_model=AnalysisResultResponse)
async def get_analysis(
    answer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取分析结果"""
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.answer_id == answer_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在或仍在处理中")
    return AnalysisResultResponse.model_validate(analysis)


@router.get("/{answer_id}/analysis/stream")
async def stream_analysis(
    answer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """SSE 流式分析"""
    # 检查 Answer 是否存在
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.question))
        .where(Answer.id == answer_id)
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="作答记录不存在")

    # 检查是否已有分析结果
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.answer_id == answer_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        async def return_existing():
            yield f"event: done\ndata: {json.dumps({'score': existing.score, 'full_content': existing.feedback}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            return_existing(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, no-transform",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Content-Encoding": "none",
            }
        )

    # 检查是否正在分析
    if analysis_locks.get(answer_id):
        raise HTTPException(status_code=409, detail="分析正在进行中")

    analysis_locks[answer_id] = True

    async def generate():
        full_content = ""
        model_name = ""
        try:
            async with async_session_maker() as stream_db:
                service = AnalyzeService(stream_db)
                model_config = await service.get_active_model()
                if not model_config:
                    yield f"event: error\ndata: {json.dumps({'message': '未配置激活的分析模型'}, ensure_ascii=False)}\n\n"
                    return
                model_name = model_config.model_name

                async for chunk in service.analyze_answer_stream(
                    question=answer.question.content,
                    answer=answer.transcript or "",
                    duration=answer.duration_seconds or 0,
                    prompt_type="single_analyze"
                ):
                    full_content += chunk
                    yield f"event: token\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                # 提取分数
                score = None
                score_match = re.search(r"总体评分[：:]\s*(\d+(?:\.\d+)?)", full_content)
                if score_match:
                    score = float(score_match.group(1))

                # 保存分析结果
                analysis = AnalysisResult(
                    answer_id=answer_id,
                    analysis_type="single",
                    score=score,
                    feedback=full_content,
                    model_name=model_name
                )
                stream_db.add(analysis)
                await stream_db.commit()

                yield f"event: done\ndata: {json.dumps({'score': score, 'full_content': full_content}, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            # 客户端断开，继续后台保存
            if full_content:
                asyncio.create_task(save_partial_analysis(answer_id, full_content, model_name))
        except Exception as e:
            logger.error(f"流式分析失败: answer_id={answer_id}, error={e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            analysis_locks.pop(answer_id, None)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
        }
    )


async def save_partial_analysis(answer_id: int, content: str, model_name: str):
    """后台保存部分分析结果"""
    async with async_session_maker() as db:
        try:
            score = None
            score_match = re.search(r"总体评分[：:]\s*(\d+(?:\.\d+)?)", content)
            if score_match:
                score = float(score_match.group(1))

            analysis = AnalysisResult(
                answer_id=answer_id,
                analysis_type="single",
                score=score,
                feedback=content,
                model_name=model_name
            )
            db.add(analysis)
            await db.commit()
            logger.info(f"后台保存分析结果: answer_id={answer_id}")
        except Exception as e:
            logger.error(f"后台保存失败: answer_id={answer_id}, error={e}")


@router.post("/history-analyze")
async def analyze_history(
    data: HistoryAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """历史综合分析（不保存）"""
    if not data.answer_ids:
        raise HTTPException(status_code=400, detail="请选择至少一条记录")

    # 查询历史记录
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.analysis), selectinload(Answer.question))
        .where(Answer.id.in_(data.answer_ids))
        .order_by(Answer.created_at)
    )
    answers = result.scalars().all()

    if not answers:
        raise HTTPException(status_code=404, detail="未找到记录")

    # 构建历史数据
    history_lines = []
    for a in answers:
        score = a.analysis.score if a.analysis else "无"
        history_lines.append(
            f"日期: {a.practice_date}\n"
            f"题目: {a.question.content[:100]}...\n"
            f"作答: {(a.transcript or '')[:200]}...\n"
            f"得分: {score}\n"
            f"---"
        )

    history_data = "\n".join(history_lines)

    service = AnalyzeService(db)
    try:
        result = await service.analyze_history(
            history_data=history_data,
            prompt_type=data.analysis_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"feedback": result["feedback"], "model_name": result["model_name"]}


@router.post("/paper-analyze")
async def analyze_paper_session(
    data: PaperAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """套卷整体分析（不保存）"""
    if not data.paper_session_id:
        raise HTTPException(status_code=400, detail="请提供套卷会话ID")

    # 查询该会话的所有作答
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.question))
        .where(Answer.paper_session_id == data.paper_session_id)
        .order_by(Answer.created_at)
    )
    answers = result.scalars().all()

    if not answers:
        raise HTTPException(status_code=404, detail="未找到套卷作答记录")

    # 构建套卷内容
    paper_content_lines = []
    time_details_lines = []
    total_duration = 0

    for idx, a in enumerate(answers, 1):
        question_text = a.question.content if a.question else "未知题目"
        answer_text = a.transcript or "未作答"
        duration = a.duration_seconds or 0
        total_duration += duration

        paper_content_lines.append(
            f"### 第 {idx} 题\n"
            f"**题目**: {question_text}\n"
            f"**作答**: {answer_text}\n"
        )
        time_details_lines.append(f"第 {idx} 题: {duration} 秒")

    paper_content = "\n".join(paper_content_lines)
    time_details = "\n".join(time_details_lines)

    service = AnalyzeService(db)
    try:
        result = await service.analyze_paper(
            paper_content=paper_content,
            time_details=time_details,
            total_time=total_duration
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"feedback": result["feedback"], "model_name": result["model_name"]}


# 套卷分析锁
paper_analysis_locks: dict[str, bool] = {}


@router.get("/paper-analyze/stream/{session_id}")
async def stream_paper_analysis(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """套卷流式分析（SSE）"""
    if not session_id:
        raise HTTPException(status_code=400, detail="请提供套卷会话ID")

    # 检查是否正在分析
    if paper_analysis_locks.get(session_id):
        raise HTTPException(status_code=409, detail="分析正在进行中")

    # 查询该会话的所有作答
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.question))
        .where(Answer.paper_session_id == session_id)
        .order_by(Answer.created_at)
    )
    answers = result.scalars().all()

    if not answers:
        raise HTTPException(status_code=404, detail="未找到套卷作答记录")

    # 构建套卷内容
    paper_content_lines = []
    time_details_lines = []
    total_duration = 0

    for idx, a in enumerate(answers, 1):
        question_text = a.question.content if a.question else "未知题目"
        answer_text = a.transcript or "未作答"
        duration = a.duration_seconds or 0
        total_duration += duration

        paper_content_lines.append(
            f"### 第 {idx} 题\n"
            f"**题目**: {question_text}\n"
            f"**作答**: {answer_text}\n"
        )
        time_details_lines.append(f"第 {idx} 题: {duration} 秒")

    paper_content = "\n".join(paper_content_lines)
    time_details = "\n".join(time_details_lines)

    paper_analysis_locks[session_id] = True

    async def generate():
        full_content = ""
        try:
            async with async_session_maker() as stream_db:
                service = AnalyzeService(stream_db)
                model_config = await service.get_active_model()
                if not model_config:
                    yield f"event: error\ndata: {json.dumps({'message': '未配置激活的分析模型'}, ensure_ascii=False)}\n\n"
                    return

                async for chunk in service.analyze_paper_stream(
                    paper_content=paper_content,
                    time_details=time_details,
                    total_time=total_duration
                ):
                    full_content += chunk
                    yield f"event: token\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                yield f"event: done\ndata: {json.dumps({'full_content': full_content}, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info(f"套卷分析被取消: session_id={session_id}")
        except Exception as e:
            logger.error(f"套卷流式分析失败: session_id={session_id}, error={e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            paper_analysis_locks.pop(session_id, None)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
        }
    )