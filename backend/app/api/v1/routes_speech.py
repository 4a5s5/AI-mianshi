from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import base64
from ...core.database import get_db
from ...models.config import SpeechConfig
from ...schemas.config import SpeechConfigUpdate

router = APIRouter(prefix="/speech", tags=["语音配置"])


@router.get("/config")
async def get_speech_config(
    db: AsyncSession = Depends(get_db)
):
    """获取语音配置"""
    result = await db.execute(select(SpeechConfig))
    config = result.scalar_one_or_none()
    if not config:
        # 返回默认配置
        return {
            "id": 0,
            "provider": "web_speech",
            "whisper_api_url": None,
            "whisper_api_key": None,
            "is_active": True
        }
    return {
        "id": config.id,
        "provider": config.provider,
        "whisper_api_url": config.whisper_api_url,
        "whisper_api_key": "***" if config.whisper_api_key else None,  # 脱敏
        "is_active": config.is_active
    }


@router.put("/config")
async def update_speech_config(
    data: SpeechConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新语音配置"""
    result = await db.execute(select(SpeechConfig))
    config = result.scalar_one_or_none()

    if not config:
        config = SpeechConfig(
            provider=data.provider or "web_speech",
            whisper_api_url=data.whisper_api_url,
            whisper_api_key=data.whisper_api_key
        )
        db.add(config)
    else:
        if data.provider is not None:
            config.provider = data.provider
        if data.whisper_api_url is not None:
            config.whisper_api_url = data.whisper_api_url
        if data.whisper_api_key is not None and data.whisper_api_key != "***":
            config.whisper_api_key = data.whisper_api_key

    await db.commit()
    await db.refresh(config)
    return {
        "id": config.id,
        "provider": config.provider,
        "whisper_api_url": config.whisper_api_url,
        "is_active": config.is_active
    }


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """使用 Whisper API 转写音频"""
    # 获取配置
    result = await db.execute(select(SpeechConfig))
    config = result.scalar_one_or_none()

    if not config or config.provider != "whisper":
        raise HTTPException(status_code=400, detail="Whisper 未配置或未启用")

    if not config.whisper_api_url or not config.whisper_api_key:
        raise HTTPException(status_code=400, detail="Whisper API URL 或 Key 未配置")

    # 读取音频文件
    audio_content = await file.read()

    # 确定文件格式
    content_type = file.content_type or "audio/webm"
    filename = file.filename or "audio.webm"

    # 调用 Whisper API
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # OpenAI Whisper API 格式
            url = f"{config.whisper_api_url.rstrip('/')}/audio/transcriptions"

            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {config.whisper_api_key}"
                },
                files={
                    "file": (filename, audio_content, content_type)
                },
                data={
                    "model": "whisper-1",
                    "language": "zh",
                    "response_format": "json"
                }
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Whisper API 错误: {response.text}"
                )

            result_data = response.json()
            transcript = result_data.get("text", "")

            return {"transcript": transcript}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Whisper API 超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转写失败: {str(e)}")
