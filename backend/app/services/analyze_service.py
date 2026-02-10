from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncIterator
from ..models.config import ModelConfig, Prompt
from .ai_client import AIClient


class AnalyzeService:
    """作答分析服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_model(self) -> ModelConfig | None:
        """获取激活的分析模型配置"""
        result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.role == "analyze",
                ModelConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_prompt(self, prompt_type: str) -> Prompt | None:
        """获取指定类型的提示词"""
        result = await self.db.execute(
            select(Prompt).where(Prompt.prompt_type == prompt_type)
        )
        return result.scalar_one_or_none()

    async def analyze_answer(
        self,
        question: str,
        answer: str,
        duration: int,
        prompt_type: str = "single_analyze"
    ) -> dict:
        """分析单题作答"""
        model_config = await self.get_active_model()
        if not model_config:
            raise ValueError("未配置激活的分析模型")

        prompt = await self.get_prompt(prompt_type)
        if not prompt:
            raise ValueError(f"未找到提示词类型: {prompt_type}")

        # 替换提示词中的变量
        user_message = prompt.content.replace("{question}", question)
        user_message = user_message.replace("{answer}", answer)
        user_message = user_message.replace("{duration}", str(duration))

        # 调用 AI
        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        response = await client.chat(
            system_prompt="你是一位资深的公务员面试考官。",
            user_message=user_message
        )

        return {
            "feedback": response,
            "model_name": model_config.model_name
        }

    async def analyze_answer_stream(
        self,
        question: str,
        answer: str,
        duration: int,
        prompt_type: str = "single_analyze"
    ) -> AsyncIterator[str]:
        """流式分析单题作答"""
        model_config = await self.get_active_model()
        if not model_config:
            raise ValueError("未配置激活的分析模型")

        prompt = await self.get_prompt(prompt_type)
        if not prompt:
            raise ValueError(f"未找到提示词类型: {prompt_type}")

        user_message = prompt.content.replace("{question}", question)
        user_message = user_message.replace("{answer}", answer)
        user_message = user_message.replace("{duration}", str(duration))

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        async for chunk in client.chat_stream(
            system_prompt="你是一位资深的公务员面试考官。",
            user_message=user_message
        ):
            yield chunk

    async def analyze_history(
        self,
        history_data: str,
        prompt_type: str
    ) -> dict:
        """分析历史作答"""
        model_config = await self.get_active_model()
        if not model_config:
            raise ValueError("未配置激活的分析模型")

        prompt = await self.get_prompt(prompt_type)
        if not prompt:
            raise ValueError(f"未找到提示词类型: {prompt_type}")

        user_message = prompt.content.replace("{history_records}", history_data)

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        response = await client.chat(
            system_prompt="你是一位资深的公务员面试教练。",
            user_message=user_message
        )

        return {
            "feedback": response,
            "model_name": model_config.model_name
        }

    async def analyze_paper(
        self,
        paper_content: str,
        time_details: str,
        total_time: int
    ) -> dict:
        """分析套卷作答"""
        model_config = await self.get_active_model()
        if not model_config:
            raise ValueError("未配置激活的分析模型")

        prompt = await self.get_prompt("paper_analyze")
        if not prompt:
            raise ValueError("未找到套卷分析提示词")

        user_message = prompt.content.replace("{paper_content}", paper_content)
        user_message = user_message.replace("{time_details}", time_details)
        user_message = user_message.replace("{total_time}", str(total_time))

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        response = await client.chat(
            system_prompt="你是一位资深的公务员面试考官。",
            user_message=user_message
        )

        return {
            "feedback": response,
            "model_name": model_config.model_name
        }

    async def analyze_paper_stream(
        self,
        paper_content: str,
        time_details: str,
        total_time: int
    ) -> AsyncIterator[str]:
        """流式分析套卷作答"""
        model_config = await self.get_active_model()
        if not model_config:
            raise ValueError("未配置激活的分析模型")

        prompt = await self.get_prompt("paper_analyze")
        if not prompt:
            raise ValueError("未找到套卷分析提示词")

        user_message = prompt.content.replace("{paper_content}", paper_content)
        user_message = user_message.replace("{time_details}", time_details)
        user_message = user_message.replace("{total_time}", str(total_time))

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        async for chunk in client.chat_stream(
            system_prompt="你是一位资深的公务员面试考官。",
            user_message=user_message
        ):
            yield chunk
