from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...core.database import get_db
from ...models.question import Question
from ...schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    BatchDeleteRequest,
    BatchDeleteResponse
)

router = APIRouter(prefix="/questions", tags=["题库管理"])


@router.get("", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    keyword: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """分页查询题目"""
    query = select(Question).where(Question.is_deleted == False)

    if category:
        categories = [c.strip() for c in category.split(",") if c.strip()]
        if len(categories) == 1:
            query = query.where(Question.category == categories[0])
        elif len(categories) > 1:
            query = query.where(Question.category.in_(categories))

    if keyword:
        query = query.where(
            Question.content.contains(keyword) |
            Question.analysis.contains(keyword) |
            Question.reference_answer.contains(keyword) |
            Question.tags.contains(keyword)
        )

    # 总数
    count_query = select(func.count(Question.id)).where(Question.is_deleted == False)
    if category:
        categories = [c.strip() for c in category.split(",") if c.strip()]
        if len(categories) == 1:
            count_query = count_query.where(Question.category == categories[0])
        elif len(categories) > 1:
            count_query = count_query.where(Question.category.in_(categories))
    if keyword:
        count_query = count_query.where(
            Question.content.contains(keyword) |
            Question.analysis.contains(keyword) |
            Question.reference_answer.contains(keyword) |
            Question.tags.contains(keyword)
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    query = query.order_by(Question.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    questions = result.scalars().all()

    return QuestionListResponse(
        items=[QuestionResponse.model_validate(q) for q in questions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=QuestionResponse)
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """新增题目"""
    obj_data = data.model_dump()
    obj_data["source"] = "manual"
    question = Question(**obj_data)
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return QuestionResponse.model_validate(question)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取题目详情"""
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return QuestionResponse.model_validate(question)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新题目"""
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)

    await db.commit()
    await db.refresh(question)
    return QuestionResponse.model_validate(question)


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除题目（软删除）"""
    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.is_deleted == False)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question.is_deleted = True
    await db.commit()
    return {"message": "删除成功"}


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_questions(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量删除题目（软删除）"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的题目")

    result = await db.execute(
        select(Question).where(
            Question.id.in_(data.ids),
            Question.is_deleted == False
        )
    )
    questions = result.scalars().all()

    for q in questions:
        q.is_deleted = True

    await db.commit()
    return BatchDeleteResponse(deleted_count=len(questions))


@router.get("/random/single", response_model=QuestionResponse)
async def random_question(
    category: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """随机抽取一道题目"""
    query = select(Question).where(Question.is_deleted == False)
    if category:
        query = query.where(Question.category == category)
    query = query.order_by(func.random()).limit(1)

    result = await db.execute(query)
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题库为空")
    return QuestionResponse.model_validate(question)
