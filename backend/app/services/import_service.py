from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from ..models.config import ModelConfig, Prompt
from ..models.question import Question
from ..models.paper import Paper, PaperItem
from ..models.import_task import ImportTask
from .ai_client import AIClient


class ImportService:
    """题库导入服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_import_model(self) -> ModelConfig | None:
        """获取激活的导入模型配置"""
        result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.role == "import",
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

    async def parse_single_questions(self, document_content: str) -> list[dict]:
        """解析单题文档"""
        model_config = await self.get_active_import_model()
        if not model_config:
            raise ValueError("未配置激活的导入模型")

        prompt = await self.get_prompt("import_single")
        if not prompt:
            raise ValueError("未找到单题导入提示词")

        user_message = prompt.content.replace("{document_content}", document_content)

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        response = await client.chat(
            system_prompt="你是一个专业的题目解析助手，请严格按照 JSON 格式输出。",
            user_message=user_message,
            temperature=0.3
        )

        # 尝试解析 JSON
        try:
            # 清理可能的 markdown 代码块
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            questions = json.loads(cleaned)
            if not isinstance(questions, list):
                questions = [questions]
            return questions
        except json.JSONDecodeError as e:
            raise ValueError(f"AI 返回格式错误: {str(e)}")

    async def parse_paper(self, file_name: str, document_content: str) -> dict:
        """解析套卷文档"""
        model_config = await self.get_active_import_model()
        if not model_config:
            raise ValueError("未配置激活的导入模型")

        prompt = await self.get_prompt("import_paper")
        if not prompt:
            raise ValueError("未找到套卷导入提示词")

        user_message = prompt.content.replace("{file_name}", file_name)
        user_message = user_message.replace("{document_content}", document_content)

        client = AIClient(
            base_url=model_config.base_url,
            api_key=model_config.api_key,
            model_name=model_config.model_name
        )

        response = await client.chat(
            system_prompt="你是一个专业的题目解析助手，请严格按照 JSON 格式输出。",
            user_message=user_message,
            temperature=0.3
        )

        # 尝试解析 JSON
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI 返回格式错误: {str(e)}")

    async def import_single_questions(self, parsed_questions: list[dict]) -> int:
        """导入单题到题库"""
        count = 0
        for q in parsed_questions:
            if not q.get("content"):
                continue
            question = Question(
                category=q.get("category", "未分类"),
                content=q["content"],
                analysis=q.get("analysis"),
                reference_answer=q.get("reference_answer"),
                source="import"
            )
            self.db.add(question)
            count += 1

        await self.db.commit()
        return count

    async def import_paper(self, parsed_paper: dict) -> tuple[int, int]:
        """导入套卷"""
        paper_title = parsed_paper.get("paper_title", "导入套卷")
        questions_data = parsed_paper.get("questions", [])

        # 创建套卷
        paper = Paper(
            title=paper_title,
            description="通过文档导入"
        )
        self.db.add(paper)
        await self.db.flush()

        # 创建题目并关联
        question_count = 0
        for idx, q in enumerate(questions_data):
            if not q.get("content"):
                continue

            # 创建题目
            question = Question(
                category=q.get("category", "未分类"),
                content=q["content"],
                analysis=q.get("analysis"),
                reference_answer=q.get("reference_answer"),
                source="import"
            )
            self.db.add(question)
            await self.db.flush()

            # 关联到套卷
            item = PaperItem(
                paper_id=paper.id,
                question_id=question.id,
                sort_order=idx + 1
            )
            self.db.add(item)
            question_count += 1

        await self.db.commit()
        return paper.id, question_count
