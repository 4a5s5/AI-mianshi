from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...models.config import Prompt
from ...schemas.config import PromptUpdate, PromptResponse

router = APIRouter(prefix="/prompts", tags=["提示词管理"])


@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    db: AsyncSession = Depends(get_db)
):
    """获取所有提示词"""
    result = await db.execute(select(Prompt))
    prompts = result.scalars().all()
    return [PromptResponse.model_validate(p) for p in prompts]


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取提示词详情"""
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return PromptResponse.model_validate(prompt)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新提示词"""
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)

    await db.commit()
    await db.refresh(prompt)
    return PromptResponse.model_validate(prompt)
