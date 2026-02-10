from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...models.config import ModelConfig, Prompt, SpeechConfig
from ...schemas.config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    PromptUpdate,
    PromptResponse,
    SpeechConfigBase,
    SpeechConfigResponse,
    FetchModelsRequest,
    FetchModelsResponse
)
from ...services.ai_client import AIClient

router = APIRouter(prefix="/models", tags=["模型配置"])


@router.get("", response_model=list[ModelConfigResponse])
async def list_models(
    role: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取模型配置列表"""
    query = select(ModelConfig)
    if role:
        query = query.where(ModelConfig.role == role)
    query = query.order_by(ModelConfig.created_at.desc())

    result = await db.execute(query)
    configs = result.scalars().all()
    return [ModelConfigResponse.model_validate(c) for c in configs]


@router.post("", response_model=ModelConfigResponse)
async def create_model(
    data: ModelConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """新增模型配置"""
    config = ModelConfig(**data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return ModelConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model(
    config_id: int,
    data: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return ModelConfigResponse.model_validate(config)


@router.delete("/{config_id}")
async def delete_model(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    await db.delete(config)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/{config_id}/activate")
async def activate_model(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """激活模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 取消同角色其他配置的激活状态
    await db.execute(
        select(ModelConfig).where(
            ModelConfig.role == config.role,
            ModelConfig.id != config_id
        )
    )
    same_role_result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.role == config.role,
            ModelConfig.id != config_id
        )
    )
    for other in same_role_result.scalars().all():
        other.is_active = False

    config.is_active = True
    await db.commit()
    return {"message": "激活成功"}


@router.post("/fetch-models", response_model=FetchModelsResponse)
async def fetch_models(data: FetchModelsRequest):
    """获取可用模型列表"""
    try:
        models = await AIClient.fetch_models(data.base_url, data.api_key)
        return FetchModelsResponse(models=models)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取模型列表失败: {str(e)}")
