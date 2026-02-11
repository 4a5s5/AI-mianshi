from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .core.database import async_session_maker
from .models.config import Prompt, SpeechConfig, SystemConfig

# 默认提示词模板
DEFAULT_PROMPTS = [
    {
        "prompt_type": "single_analyze",
        "title": "单题作答分析",
        "content": """你是一位资深的公务员面试考官，精通天津省考结构化面试评分规则。请根据以下评分细则对考生的作答进行全面分析：

## 评分细则
1. 语言表达 (权重15分)：口齿清晰度、用词准确性、逻辑条理性
   - 好 (08-10分)：表述流畅准确，逻辑性极强
   - 中 (04-07分)：基本能够清晰表达，逻辑尚可
   - 差 (00-03分)：表达含糊不清，缺乏逻辑感

2. 综合分析能力 (权重20分)：问题剖析深度、根源认识、对策可行性
   - 好 (15-20分)：分析深刻入微，对策具体可行，有创新见解
   - 中 (07-14分)：分析较为全面，能够提出基本对策
   - 差 (00-06分)：看待问题表面化，无法提供有效建议

3. 应变能力 (权重20分)：情绪稳定性、反应敏捷度、解决方案有效性
   - 好 (15-20分)：反应极其敏捷，压力下表现从容，解决手段高明
   - 中 (07-14分)：反应基本跟得上，能给出常规解决办法
   - 差 (00-06分)：反应迟钝或由于压力导致情绪波动

4. 人际交往能力 (权重15分)：合作意识、沟通有效性、原则性
   - 好 (15-20分)：沟通自然有效，具备极强的团队协作意识
   - 中 (07-14分)：能够正常沟通，人际处理方式基本合规
   - 差 (00-06分)：沟通受阻，缺乏团队意识

5. 计划组织协调能力 (权重20分)：预见性、计划科学性、资源配置合理性
   - 好 (15-20分)：预见性强，计划详尽科学，资源配置非常合理
   - 中 (07-14分)：有基本的计划框架，能考虑到主要因素
   - 差 (00-06分)：缺乏组织条理，计划漏洞较多

6. 举止仪表 (权重10分)：（基于文字作答，给予基础分6分）

## 作答原则
- 问啥答啥，直截了当，开门见山
- 回到生活工作中真正解决问题
- 纵向分层：时间顺序、主体顺序（摆平所有人、事、问题）
- 横向展开：连接词+观点+分析（why）+解决（how）
- 劝说五法：动之以情、晓之以理、诱之以利、避之以害、绳之以法

## 题目
{question}

## 考生作答
{answer}

## 作答时长
{duration}秒

请按以下格式输出：

### 总体评分：X/100 分

### 各维度得分
- 语言表达：X/15
- 综合分析：X/20
- 应变能力：X/20
- 人际交往：X/15
- 计划组织：X/20
- 举止仪表：6/10

### 亮点与保持
（列出2-3条做得好的地方）

### 不足与改进
（列出2-3条需要改进的地方）

### 题目分析
（分析本题考查要点和作答逻辑）

### 模范作答
（根据作答原则生成一份高分参考答案）"""
    },
    {
        "prompt_type": "history_single_analyze",
        "title": "单题历史分析",
        "content": """你是一位资深的公务员面试教练。现在需要对考生的多次单题练习记录进行综合分析。

请按照时间顺序，分析以下练习记录：

## 练习记录
{history_records}

请按以下格式输出：

### 整体进步趋势
（分析分数变化走势，是否有明显进步或波动）

### 作答习惯总结
（识别考生的固定表达模式、常用句式、思维方式）

### 持续性不足
（指出多次出现的问题，需要重点改进的方面）

### 进步的点
（对比早期和近期，指出明显改善的方面）

### 退步的点
（如有，指出下滑的方面及可能原因）

### 针对性练习建议
（给出接下来应该重点练习的题型和方向）"""
    },
    {
        "prompt_type": "paper_analyze",
        "title": "套卷作答分析",
        "content": """你是一位资深的公务员面试考官。请对考生的套卷练习进行全面分析。

## 评分细则
（同单题分析的评分细则）

## 套卷题目与作答
{paper_content}

## 各题作答时长
{time_details}

## 总时长限制
{total_time}秒

请按以下格式输出：

### 整体评分：X/100 分

### 各题得分
（列出每道题的得分和简评）

### 时间分配分析
（分析各题时间分配是否合理，是否存在前松后紧或虎头蛇尾）

### 整体节奏把控
（评价整套试卷的作答节奏）

### 各题之间的逻辑一致性
（分析回答风格、论述深度是否一致）

### 综合建议
（给出整体改进方向）"""
    },
    {
        "prompt_type": "history_paper_analyze",
        "title": "套卷历史分析",
        "content": """你是一位资深的公务员面试教练。现在需要对考生的多次套卷练习记录进行综合分析。

## 练习记录
{history_records}

请按以下格式输出：

### 整体进步趋势
（分析套卷得分变化走势）

### 时间分配规律
（分析考生在套卷中的时间分配习惯）

### 各题型得分分布
（分析不同题型的得分表现）

### 整体把控能力变化
（评价考生对套卷节奏把控的进步情况）

### 持续性不足
（多次出现的问题）

### 针对性练习建议
（给出改进方向）"""
    },
    {
        "prompt_type": "import_single",
        "title": "单题导入解析",
        "content": """请从以下文档内容中提取面试题目信息。

## 文档内容
{document_content}

请按以下JSON格式输出（输出纯JSON，不要markdown标记）：
[
  {
    "category": "题型（综合分析/组织协调/应急应变/人际关系/自我认知）",
    "content": "题目内容",
    "analysis": "解析（如有，否则为null）",
    "reference_answer": "参考答案（如有，否则为null）"
  }
]

注意：
1. 仔细识别每道独立的题目
2. 题型根据题目内容判断
3. 如果有解析或答案，一并提取
4. 只输出JSON数组，不要其他内容"""
    },
    {
        "prompt_type": "import_paper",
        "title": "套卷导入解析",
        "content": """请从以下文档内容中提取套卷信息。

## 文档名称
{file_name}

## 文档内容
{document_content}

请按以下JSON格式输出（输出纯JSON，不要markdown标记）：
{
  "paper_title": "套卷名称（从文档名提取或根据内容命名）",
  "questions": [
    {
      "category": "题型",
      "content": "题目内容",
      "analysis": "解析（如有）",
      "reference_answer": "参考答案（如有）"
    }
  ]
}

注意：
1. 套卷名称优先使用文档名
2. 按顺序提取所有题目
3. 保持题目的原始顺序
4. 只输出JSON对象，不要其他内容"""
    }
]


async def init_default_prompts():
    """初始化默认提示词"""
    async with async_session_maker() as db:
        for prompt_data in DEFAULT_PROMPTS:
            result = await db.execute(
                select(Prompt).where(Prompt.prompt_type == prompt_data["prompt_type"])
            )
            if not result.scalar_one_or_none():
                prompt = Prompt(**prompt_data)
                db.add(prompt)

        # 初始化语音配置
        result = await db.execute(select(SpeechConfig))
        if not result.scalar_one_or_none():
            speech_config = SpeechConfig(
                provider="web_speech",
                is_active=True
            )
            db.add(speech_config)

        await db.commit()

        # 初始化系统配置
        default_sys_configs = [
            {"key": "max_import_chars", "value": "30000"},
        ]
        for cfg in default_sys_configs:
            result = await db.execute(
                select(SystemConfig).where(SystemConfig.key == cfg["key"])
            )
            if not result.scalar_one_or_none():
                db.add(SystemConfig(**cfg))

        await db.commit()
