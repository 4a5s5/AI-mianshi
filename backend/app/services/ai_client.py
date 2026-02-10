import httpx
from typing import Optional, AsyncIterator
from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, APIError


class AIClient:
    """统一的 AI 调用封装，支持 OpenAI 兼容格式"""

    def __init__(self, base_url: str, api_key: str, model_name: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=http_client
        )

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """发送对话请求"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except APITimeoutError:
            raise ValueError("AI 服务响应超时，请稍后重试")
        except APIConnectionError:
            raise ValueError("AI 服务连接失败，请检查网络或配置")
        except APIError as e:
            raise ValueError(f"AI 服务错误: {str(e)}")

    async def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str]:
        """流式对话，逐块返回内容"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APITimeoutError:
            raise ValueError("AI 服务响应超时，请稍后重试")
        except APIConnectionError:
            raise ValueError("AI 服务连接失败，请检查网络或配置")
        except APIError as e:
            raise ValueError(f"AI 服务错误: {str(e)}")

    @staticmethod
    async def fetch_models(base_url: str, api_key: str) -> list[str]:
        """获取可用模型列表"""
        url = f"{base_url.rstrip('/')}/models"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            return [m.get("id", "") for m in models if m.get("id")]
