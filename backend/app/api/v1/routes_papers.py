from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from ...core.database import get_db
from ...models.paper import Paper, PaperItem
from ...models.question import Question
from ...schemas.paper import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperListResponse
)

router = APIRouter(prefix="/papers", tags=["套卷管理"])


@router.get("", response_model=PaperListResponse)
async def list_papers(
    db: AsyncSession = Depends(get_db)
):
    """获取套卷列表"""
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.items))
        .order_by(Paper.created_at.desc())
    )
    papers = result.scalars().all()

    count_result = await db.execute(select(func.count(Paper.id)))
    total = count_result.scalar()

    return PaperListResponse(
        items=[PaperResponse.model_validate(p) for p in papers],
        total=total
    )


@router.post("", response_model=PaperResponse)
async def create_paper(
    data: PaperCreate,
    db: AsyncSession = Depends(get_db)
):
    """新建套卷"""
    # 验证题目存在性
    if data.question_ids:
        result = await db.execute(
            select(Question.id).where(Question.id.in_(data.question_ids))
        )
        existing_ids = {row[0] for row in result.all()}
        missing_ids = set(data.question_ids) - existing_ids
        if missing_ids:
            raise HTTPException(
                status_code=400,
                detail=f"以下题目不存在: {sorted(missing_ids)}"
            )

    paper = Paper(
        title=data.title,
        description=data.description,
        time_limit_seconds=data.time_limit_seconds
    )
    db.add(paper)
    await db.flush()

    # 添加题目
    if data.question_ids:
        for idx, qid in enumerate(data.question_ids):
            item = PaperItem(
                paper_id=paper.id,
                question_id=qid,
                sort_order=idx + 1
            )
            db.add(item)

    await db.commit()
    await db.refresh(paper)

    # 重新加载关联
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.items))
        .where(Paper.id == paper.id)
    )
    paper = result.scalar_one()

    return PaperResponse.model_validate(paper)


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取套卷详情"""
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.items))
        .where(Paper.id == paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="套卷不存在")
    return PaperResponse.model_validate(paper)


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: int,
    data: PaperUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新套卷"""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="套卷不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(paper, key, value)

    await db.commit()
    await db.refresh(paper)
    return PaperResponse.model_validate(paper)


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除套卷"""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="套卷不存在")

    await db.delete(paper)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/{paper_id}/items")
async def add_paper_item(
    paper_id: int,
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """添加题目到套卷"""
    # 检查套卷
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="套卷不存在")

    # 检查题目
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="题目不存在")

    # 获取当前最大排序
    max_order_result = await db.execute(
        select(func.max(PaperItem.sort_order))
        .where(PaperItem.paper_id == paper_id)
    )
    max_order = max_order_result.scalar() or 0

    item = PaperItem(
        paper_id=paper_id,
        question_id=question_id,
        sort_order=max_order + 1
    )
    db.add(item)
    await db.commit()
    return {"message": "添加成功"}


@router.delete("/{paper_id}/items/{item_id}")
async def remove_paper_item(
    paper_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """从套卷移除题目"""
    result = await db.execute(
        select(PaperItem).where(
            PaperItem.id == item_id,
            PaperItem.paper_id == paper_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="题目项不存在")

    await db.delete(item)
    await db.commit()
    return {"message": "移除成功"}
