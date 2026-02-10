# AI面试助手 - 实施任务清单

> 零决策可执行计划：所有任务均可机械执行，无需额外判断

## 任务总览

| 阶段 | 任务数 | 优先级 |
|------|--------|--------|
| 后端 Bug 修复 | 7 | P0-P1 |
| 前端类型安全 | 2 | P1 |
| 前端组件重构 | 1 | P2 |

---

## 第一阶段：后端 Bug 修复

### Task BE-1: 创建作答输入验证
**文件**: `backend/app/api/v1/routes_answers.py`
**优先级**: P0

**实施步骤**:
1. 在 `create_answer` 函数开头添加 mode 验证：
   ```python
   if data.mode not in ("single", "paper"):
       raise HTTPException(status_code=400, detail="mode 必须为 single 或 paper")
   ```

2. 添加 question_id 存在性验证：
   ```python
   question = await db.execute(select(Question).where(Question.id == data.question_id))
   if not question.scalar_one_or_none():
       raise HTTPException(status_code=404, detail="题目不存在")
   ```

3. 添加 paper 模式业务规则验证：
   ```python
   if data.mode == "paper":
       if not data.paper_id or not data.paper_session_id:
           raise HTTPException(status_code=400, detail="套卷模式需要 paper_id 和 paper_session_id")
   elif data.paper_id:
       raise HTTPException(status_code=400, detail="单题模式不能传入 paper_id")
   ```

**验证方式**:
- 测试 mode 非法值返回 400
- 测试 question_id 不存在返回 404
- 测试 paper 模式缺少必填字段返回 400

---

### Task BE-2: 创建套卷题目验证
**文件**: `backend/app/api/v1/routes_papers.py`
**优先级**: P0

**实施步骤**:
1. 在 `create_paper` 函数中添加题目存在性验证：
   ```python
   if data.question_ids:
       result = await db.execute(
           select(Question.id).where(Question.id.in_(data.question_ids))
       )
       existing_ids = {row[0] for row in result.all()}
       missing_ids = set(data.question_ids) - existing_ids
       if missing_ids:
           raise HTTPException(
               status_code=400,
               detail=f"以下题目不存在: {list(missing_ids)}"
           )
   ```

**验证方式**:
- 测试包含不存在题目 ID 返回 400
- 测试全部有效 ID 成功创建

---

### Task BE-3: AI 客户端超时与异常处理
**文件**: `backend/app/services/ai_client.py`
**优先级**: P0

**实施步骤**:
1. 修改 `__init__` 添加超时配置：
   ```python
   import httpx
   from openai import AsyncOpenAI, APIError, APITimeoutError, APIConnectionError

   def __init__(self, base_url: str, api_key: str, model_name: str, timeout: int = 60):
       self.timeout = timeout
       http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
       self.client = AsyncOpenAI(
           base_url=base_url.rstrip("/"),
           api_key=api_key,
           http_client=http_client
       )
   ```

2. 修改 `chat` 方法添加异常处理：
   ```python
   async def chat(self, system_prompt: str, user_message: str, ...) -> str:
       try:
           response = await self.client.chat.completions.create(...)
           return response.choices[0].message.content
       except APITimeoutError:
           raise ValueError("AI 服务响应超时，请稍后重试")
       except APIConnectionError:
           raise ValueError("AI 服务连接失败，请检查网络或配置")
       except APIError as e:
           raise ValueError(f"AI 服务错误: {e.message}")
   ```

**验证方式**:
- 模拟超时场景返回明确错误
- 模拟网络错误返回明确错误

---

### Task BE-4: 分析结果唯一约束
**文件**: `backend/app/models/analysis.py`
**优先级**: P1

**实施步骤**:
1. 为 answer_id 添加唯一约束：
   ```python
   from sqlalchemy import UniqueConstraint

   class AnalysisResult(Base):
       __tablename__ = "analysis_results"
       __table_args__ = (
           UniqueConstraint('answer_id', name='uq_analysis_answer_id'),
       )
   ```

2. 在 routes_answers.py 的分析触发逻辑中捕获唯一约束冲突：
   ```python
   from sqlalchemy.exc import IntegrityError

   try:
       await db.commit()
   except IntegrityError:
       raise HTTPException(status_code=409, detail="该作答已有分析结果")
   ```

**验证方式**:
- 测试重复分析返回 409

---

### Task BE-5: 文件后缀大小写处理
**文件**: `backend/app/api/v1/routes_import.py`
**优先级**: P1

**实施步骤**:
1. 修改文件类型判断逻辑：
   ```python
   filename_lower = file.filename.lower() if file.filename else ""
   if filename_lower.endswith(".txt"):
       file_type = "txt"
   elif filename_lower.endswith(".pdf"):
       file_type = "pdf"
   else:
       raise HTTPException(status_code=400, detail="仅支持 TXT 和 PDF 文件")
   ```

**验证方式**:
- 测试上传 .TXT、.PDF 大写后缀成功解析

---

### Task BE-6: 业务异常捕获
**文件**: `backend/app/api/v1/routes_answers.py`
**优先级**: P1

**实施步骤**:
1. 在 `analyze_history` 函数 (约159行) 添加异常捕获：
   ```python
   try:
       result = await service.analyze_history(...)
   except ValueError as e:
       raise HTTPException(status_code=400, detail=str(e))
   ```

2. 在 `analyze_paper_session` 函数 (约203行) 添加相同处理

**验证方式**:
- 测试未配置模型时返回 400 而非 500

---

### Task BE-7: 语音配置 API 风格统一
**文件**: `backend/app/api/v1/routes_speech.py`
**优先级**: P2

**实施步骤**:
1. 创建 Pydantic schema：
   ```python
   # schemas/config.py
   class SpeechConfigUpdate(BaseModel):
       provider: Optional[str] = None
       whisper_api_url: Optional[str] = None
       whisper_api_key: Optional[str] = None
   ```

2. 修改路由使用 JSON body：
   ```python
   @router.put("/speech/config")
   async def update_speech_config(
       data: SpeechConfigUpdate,
       db: AsyncSession = Depends(get_db)
   ):
       # 使用 data.provider, data.whisper_api_url 等
   ```

**验证方式**:
- 测试 JSON body 更新配置成功

---

## 第二阶段：前端类型安全

### Task FE-1: ECharts 资源清理与类型修复
**文件**: `frontend/src/views/DashboardView.vue`
**优先级**: P1

**实施步骤**:
1. 在 `<script setup>` 中添加 chartInstance 引用：
   ```typescript
   import type { ECharts } from 'echarts'
   const chartInstance = ref<ECharts | null>(null)
   ```

2. 修改 initChart 函数保存实例：
   ```typescript
   chartInstance.value = echarts.init(chartRef.value)
   ```

3. 添加 onUnmounted 清理：
   ```typescript
   onUnmounted(() => {
     if (chartInstance.value) {
       chartInstance.value.dispose()
       chartInstance.value = null
     }
     window.removeEventListener('resize', handleResize)
   })
   ```

4. 修复 tooltip formatter 类型 (第102行)：
   ```typescript
   interface TooltipParams {
     name: string
     value: number
     dataIndex: number
   }
   formatter: (params: TooltipParams) => {
     return `${params.name}: ${params.value}分`
   }
   ```

**验证方式**:
- 快速切换页面，检查内存是否正常释放
- TypeScript 编译无 any 警告

---

### Task FE-2: 消除 any 类型
**文件**: 多个
**优先级**: P1

**实施步骤**:

1. **SettingsView.vue:301** - 定义更新类型：
   ```typescript
   interface ModelConfigUpdate {
     name?: string
     base_url?: string
     api_key?: string
     model_name?: string
   }
   const updateData: ModelConfigUpdate = { ... }
   ```

2. **RepositoryView.vue:296** - 定义文件上传类型：
   ```typescript
   import type { UploadFile } from 'element-plus'
   function handleFileChange(file: UploadFile) { ... }
   ```

3. **useRecorder.ts:25** - 扩展 Window 类型：
   创建 `frontend/src/types/global.d.ts`：
   ```typescript
   interface Window {
     SpeechRecognition: typeof SpeechRecognition
     webkitSpeechRecognition: typeof SpeechRecognition
   }
   ```

4. **useRecorder.ts:153** - 错误类型处理：
   ```typescript
   } catch (e: unknown) {
     const message = e instanceof Error ? e.message : '转写失败'
     error.value = message
   }
   ```

**验证方式**:
- 运行 `npx tsc --noEmit` 无错误
- 功能测试：设置保存、文件上传、录音转写

---

## 第三阶段：前端组件重构

### Task FE-3: SinglePracticeView 组件拆分
**文件**: `frontend/src/views/SinglePracticeView.vue`
**优先级**: P2

**实施步骤**:

1. 创建类型定义文件 `frontend/src/types/practice.ts`：
   ```typescript
   export type PracticeStep = 'select' | 'answer' | 'result'

   export interface Question {
     id: number
     content: string
     category: string
   }

   export interface AnalysisResult {
     score: number
     feedback: string
     model_answer?: string
   }
   ```

2. 创建 `frontend/src/components/practice/PracticeSelector.vue`：
   - Props: `disabled: boolean`
   - Emits: `select(question: Question)`
   - 功能：随机抽取 + 自定义输入

3. 创建 `frontend/src/components/practice/PracticeSession.vue`：
   - Props: `question: Question`
   - Emits: `complete(answer: { transcript: string, duration: number })`
   - 功能：计时器 + 录音组件

4. 创建 `frontend/src/components/practice/PracticeResult.vue`：
   - Props: `analysis: AnalysisResult`
   - Emits: `restart()`
   - 功能：分数展示 + Markdown 渲染

5. 重构 SinglePracticeView.vue：
   ```vue
   <template>
     <div class="single-practice">
       <PracticeSelector v-if="step === 'select'" @select="handleSelect" />
       <PracticeSession v-else-if="step === 'answer'" :question="question" @complete="handleComplete" />
       <PracticeResult v-else :analysis="analysis" @restart="handleRestart" />
     </div>
   </template>
   ```

**验证方式**:
- 完整跑通：选题 → 录音作答 → 查看分析 → 重新开始
- 组件间状态传递正确

---

## 执行顺序

```
BE-1 (答题验证)     ─┐
BE-2 (套卷验证)     ─┼─► BE-3 (AI超时) ─► BE-4 (唯一约束)
BE-5 (文件后缀)     ─┤
BE-6 (异常捕获)     ─┘
                            │
                            ▼
                    BE-7 (API风格) ─► FE-1 (ECharts)
                                           │
                                           ▼
                                    FE-2 (消除any) ─► FE-3 (组件拆分)
```

---

## PBT 属性 (Property-Based Testing)

| 属性 | 不变量 | 伪造策略 |
|------|--------|----------|
| 输入验证幂等性 | 相同非法输入始终返回相同错误码 | 重复发送非法请求，验证响应一致 |
| AI 超时边界 | 60秒内必须返回结果或超时错误 | 模拟慢响应，验证60秒后返回超时 |
| 分析唯一性 | 每个 answer_id 最多一条分析记录 | 并发触发分析，验证仅一条成功 |
| 类型安全 | 编译时无 any 类型 | `tsc --noEmit` 零错误 |
| 组件解耦 | 子组件不直接访问父组件状态 | 单独渲染子组件，验证 props 隔离 |

---

## 成功判据

- [x] 所有 7 个后端任务完成并通过测试
- [x] 前端 `tsc --noEmit` 零错误
- [x] ECharts 页面切换无内存泄漏
- [x] SinglePracticeView 拆分为 3 个子组件
- [ ] 完整业务流程测试通过 (待用户验证)
