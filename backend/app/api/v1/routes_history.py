from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from ...core.database import get_db
from ...models.answer import Answer
from ...models.analysis import AnalysisResult
from ...schemas.answer import AnswerWithAnalysis

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("/single")
async def get_single_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取单题练习历史（按日期分组）"""
    # 查询单题模式的作答
    query = select(Answer).where(Answer.mode == "single")
    query = query.options(
        selectinload(Answer.analysis),
        selectinload(Answer.question)
    )
    query = query.order_by(Answer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    answers = result.scalars().all()

    # 按日期分组
    grouped = {}
    for a in answers:
        date = a.practice_date
        if date not in grouped:
            grouped[date] = []
        item = AnswerWithAnalysis.model_validate(a)
        item.question_content = a.question.content if a.question else None
        grouped[date].append(item)

    # 总数
    count_result = await db.execute(
        select(func.count(Answer.id)).where(Answer.mode == "single")
    )
    total = count_result.scalar()

    return {
        "items": grouped,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/paper")
async def get_paper_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取套卷练习历史（按日期分组）"""
    query = select(Answer).where(Answer.mode == "paper")
    query = query.options(
        selectinload(Answer.analysis),
        selectinload(Answer.question),
        selectinload(Answer.paper)
    )
    query = query.order_by(Answer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    answers = result.scalars().all()

    # 按日期和套卷会话分组
    grouped = {}
    for a in answers:
        date = a.practice_date
        if date not in grouped:
            grouped[date] = {}
        session_id = a.paper_session_id or "unknown"
        if session_id not in grouped[date]:
            grouped[date][session_id] = {
                "paper_title": a.paper.title if a.paper else "自定义套卷",
                "answers": []
            }
        item = AnswerWithAnalysis.model_validate(a)
        item.question_content = a.question.content if a.question else None
        grouped[date][session_id]["answers"].append(item)

    count_result = await db.execute(
        select(func.count(Answer.id)).where(Answer.mode == "paper")
    )
    total = count_result.scalar()

    return {
        "items": grouped,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/trends")
async def get_score_trends(
    mode: str = Query("single"),
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """获取分数趋势数据"""
    from datetime import datetime, timedelta

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 查询有分析结果的作答
    query = select(Answer, AnalysisResult).join(
        AnalysisResult, Answer.id == AnalysisResult.answer_id
    ).where(
        Answer.mode == mode,
        Answer.practice_date >= start_date,
        AnalysisResult.score.isnot(None)
    ).order_by(Answer.practice_date)

    result = await db.execute(query)
    rows = result.all()

    # 按日期聚合
    daily_scores = {}
    for answer, analysis in rows:
        date = answer.practice_date
        if date not in daily_scores:
            daily_scores[date] = {"scores": [], "count": 0}
        daily_scores[date]["scores"].append(analysis.score)
        daily_scores[date]["count"] += 1

    # 计算每日平均分
    trends = []
    for date, data in sorted(daily_scores.items()):
        avg_score = sum(data["scores"]) / len(data["scores"])
        trends.append({
            "date": date,
            "avg_score": round(avg_score, 1),
            "count": data["count"]
        })

    return {"trends": trends, "mode": mode}
