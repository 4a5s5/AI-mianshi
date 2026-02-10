from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from PyPDF2 import PdfReader
import io
from ...core.database import get_db, async_session_maker
from ...models.import_task import ImportTask
from ...services.import_service import ImportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["题库导入"])


async def extract_text_from_file(file: UploadFile) -> str:
    """从文件提取文本"""
    content = await file.read()
    filename_lower = (file.filename or "").lower()

    if filename_lower.endswith('.txt'):
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("无法识别文件编码")

    elif filename_lower.endswith('.pdf'):
        try:
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"PDF 解析失败: {str(e)}")

    else:
        raise ValueError("不支持的文件格式，请上传 TXT 或 PDF 文件")


async def run_import_task(import_id: int, import_type: str, file_name: str, raw_text: str):
    """后台导入任务"""
    async with async_session_maker() as db:
        try:
            # 更新状态为运行中
            result = await db.execute(
                select(ImportTask).where(ImportTask.id == import_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return

            task.status = "running"
            await db.commit()

            service = ImportService(db)

            if import_type == "single":
                # 解析单题
                questions = await service.parse_single_questions(raw_text)
                count = await service.import_single_questions(questions)
                task.status = "success"
                task.result_summary = f"成功导入 {count} 道题目"
            else:
                # 解析套卷
                paper_data = await service.parse_paper(file_name, raw_text)
                paper_id, count = await service.import_paper(paper_data)
                task.status = "success"
                task.result_summary = f"成功创建套卷，包含 {count} 道题目"

            await db.commit()
            logger.info(f"导入任务完成: import_id={import_id}, result={task.result_summary}")

        except Exception as e:
            logger.error(f"导入任务失败: import_id={import_id}, error={e}")
            # 更新失败状态
            result = await db.execute(
                select(ImportTask).where(ImportTask.id == import_id)
            )
            task = result.scalar_one_or_none()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                await db.commit()


@router.post("/single")
async def import_single_questions(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """导入单题"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")

    try:
        raw_text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 创建导入任务
    task = ImportTask(
        file_name=file.filename,
        file_type=file.filename.split('.')[-1].lower(),
        import_type="single",
        status="pending",
        raw_text=raw_text[:50000]  # 限制存储长度
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 后台执行
    background_tasks.add_task(run_import_task, task.id, "single", file.filename, raw_text)

    return {
        "message": "导入任务已提交",
        "import_id": task.id,
        "file_name": file.filename
    }


@router.post("/paper")
async def import_paper(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """导入套卷"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")

    try:
        raw_text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 创建导入任务
    task = ImportTask(
        file_name=file.filename,
        file_type=file.filename.split('.')[-1].lower(),
        import_type="paper",
        status="pending",
        raw_text=raw_text[:50000]
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 后台执行
    background_tasks.add_task(run_import_task, task.id, "paper", file.filename, raw_text)

    return {
        "message": "导入任务已提交",
        "import_id": task.id,
        "file_name": file.filename
    }


@router.get("/status/{import_id}")
async def get_import_status(
    import_id: int,
    db: AsyncSession = Depends(get_db)
):
    """查询导入状态"""
    result = await db.execute(
        select(ImportTask).where(ImportTask.id == import_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="导入任务不存在")

    return {
        "id": task.id,
        "file_name": task.file_name,
        "import_type": task.import_type,
        "status": task.status,
        "result_summary": task.result_summary,
        "error_message": task.error_message
    }


@router.get("/history")
async def get_import_history(
    db: AsyncSession = Depends(get_db)
):
    """获取导入历史"""
    result = await db.execute(
        select(ImportTask).order_by(ImportTask.created_at.desc()).limit(20)
    )
    tasks = result.scalars().all()

    return [
        {
            "id": t.id,
            "file_name": t.file_name,
            "import_type": t.import_type,
            "status": t.status,
            "result_summary": t.result_summary,
            "error_message": t.error_message,
            "created_at": t.created_at.isoformat()
        }
        for t in tasks
    ]
