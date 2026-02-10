# UX Improvements V2 - 实施任务

## 实施顺序

1. Issue 4: 移动端题库入口（最快见效）
2. Issue 1: API 密钥持久化（基础配置）
3. Issue 2: 自由输入题目入库（数据链路）
4. Issue 3: SSE 流式输出（最复杂）

---

## Task 1: 移动端题库入口

### Task 1.1: 修改 App.vue 添加题库导航

**文件**: `frontend/src/App.vue`

**变更**:
```vue
<!-- 在练习和记录之间添加 -->
<router-link to="/repository" class="tab-item" :class="{ active: currentRoute === '/repository' }">
  <el-icon><Folder /></el-icon>
  <span>题库</span>
</router-link>
```

**具体位置**: 第 55-59 行之间（练习后、记录前）

**验收**: 移动端（宽度<768px）显示 5 个导航项，点击题库可正常跳转

---

## Task 2: API 密钥持久化

### Task 2.1: 后端 - ModelConfig 添加脱敏属性

**文件**: `backend/app/models/config.py`

**变更**:
```python
@property
def api_key_masked(self) -> str | None:
    """返回脱敏后的 API 密钥"""
    if not self.api_key:
        return None
    key = self.api_key
    if len(key) < 8:
        return "***"
    return f"{key[:3]}...{key[-4:]}"
```

### Task 2.2: 后端 - ModelConfigResponse 添加字段

**文件**: `backend/app/schemas/config.py`

**变更**:
```python
class ModelConfigResponse(BaseModel):
    id: int
    name: str
    base_url: str
    model_name: str
    role: str
    is_active: bool
    api_key_masked: str | None = None  # 新增
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Task 2.3: 前端 - SettingsView 编辑显示脱敏值

**文件**: `frontend/src/views/SettingsView.vue`

**变更**:
1. 在 `editModel` 函数中保存 `api_key_masked` 到临时变量
2. 修改 API Key 输入框的 placeholder 为脱敏值或提示文案
3. 添加辅助文案："留空则保持原密钥"

**验收**: 编辑已配置模型时，密钥框显示占位符，保存后密钥不丢失

---

## Task 3: 自由输入题目入库

### Task 3.1: 后端 - QuestionCreate 设置默认分类

**文件**: `backend/app/schemas/question.py`

**变更**:
```python
class QuestionCreate(BaseModel):
    content: str
    category: str = "自定义"  # 设置默认值
    analysis: str | None = None
    reference_answer: str | None = None
    tags: str | None = None
```

### Task 3.2: 前端 - handleCustom 异步创建题目

**文件**: `frontend/src/views/SinglePracticeView.vue`

**变更**:
```typescript
// 原 handleCustom 改为异步
async function handleCustom() {
  if (!customContent.value.trim()) {
    ElMessage.warning('请输入题目内容')
    return
  }

  customLoading.value = true  // 新增 loading 状态
  try {
    // 先创建题目
    const question = await questionApi.create({
      content: customContent.value.trim(),
      category: '自定义'
    })
    currentQuestion.value = question
    currentStep.value = 'answer'
  } catch (e) {
    ElMessage.error('题目保存失败，请重试')
  } finally {
    customLoading.value = false
  }
}
```

**新增变量**: `const customLoading = ref(false)`

**验收**: 自由输入题目后，题库管理中可查到该题目

---

## Task 4: SSE 流式输出

### Task 4.1: 后端 - AIClient 添加流式方法

**文件**: `backend/app/services/ai_client.py`

**变更**:
```python
async def chat_stream(self, messages: list[dict]) -> AsyncIterator[str]:
    """流式对话，逐块返回内容"""
    try:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        raise AIClientError(f"流式请求失败: {e}")
```

### Task 4.2: 后端 - AnalyzeService 添加流式分析

**文件**: `backend/app/services/analyze_service.py`

**变更**:
```python
async def analyze_answer_stream(
    self,
    answer: Answer,
    question: Question,
    prompt_content: str
) -> AsyncIterator[str]:
    """流式分析作答，逐块返回"""
    messages = self._build_messages(answer, question, prompt_content)
    full_content = ""
    async for chunk in self.ai_client.chat_stream(messages):
        full_content += chunk
        yield chunk
    # 返回完整内容用于后续处理
    return full_content
```

### Task 4.3: 后端 - 新增 SSE 端点

**文件**: `backend/app/api/v1/routes_answers.py`

**变更**:
```python
from fastapi.responses import StreamingResponse
import asyncio

# 分析锁（简单实现，生产环境建议用 Redis）
analysis_locks: dict[int, bool] = {}

@router.get("/{answer_id}/analysis/stream")
async def stream_analysis(
    answer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """SSE 流式分析"""
    # 检查 Answer 是否存在
    answer = await get_answer_or_404(answer_id, db)

    # 检查是否已有分析结果
    existing = await get_analysis_result(answer_id, db)
    if existing:
        return StreamingResponse(
            iter([f"event: done\ndata: {json.dumps({'score': existing.score, 'full_content': existing.content})}\n\n"]),
            media_type="text/event-stream"
        )

    # 检查是否正在分析
    if analysis_locks.get(answer_id):
        raise HTTPException(status_code=409, detail="分析正在进行中")

    analysis_locks[answer_id] = True

    async def generate():
        try:
            # 流式分析逻辑
            async for chunk in analyze_service.analyze_answer_stream(...):
                yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"

            # 保存结果
            result = await save_analysis_result(...)
            yield f"event: done\ndata: {json.dumps({'score': result.score, 'full_content': result.content})}\n\n"
        except asyncio.CancelledError:
            # 客户端断开，继续后台分析
            asyncio.create_task(continue_analysis_in_background(answer_id))
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
        finally:
            analysis_locks.pop(answer_id, None)

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Task 4.4: 前端 - 修复错误弹窗

**文件**: `frontend/src/api/request.ts`

**变更**:
```typescript
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 检查是否静默模式
    if (error.config?._silent) {
      return Promise.reject(error)
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)
```

### Task 4.5: 前端 - 实现 SSE 消费

**文件**: `frontend/src/views/SinglePracticeView.vue`

**变更**:
```typescript
const isStreaming = ref(false)
const streamContent = ref('')

async function startStreamAnalysis(answerId: number) {
  isStreaming.value = true
  streamContent.value = ''

  try {
    const response = await fetch(`/api/v1/answers/${answerId}/analysis/stream`)

    if (response.status === 409) {
      ElMessage.warning('分析正在进行中，请稍候')
      return
    }

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.content) {
            streamContent.value += data.content
          }
          if (data.full_content) {
            // 分析完成
            analysisResult.value = {
              content: data.full_content,
              score: data.score
            }
          }
        }
      }
    }
  } catch (e) {
    ElMessage.error('分析请求失败')
  } finally {
    isStreaming.value = false
  }
}
```

**验收**:
1. AI 分析过程中无错误弹窗
2. 能实时看到 AI 回复内容
3. 分析完成后显示完整结果和分数

---

## 验收检查清单

- [x] Issue 4: 移动端显示题库入口，点击正常跳转
- [x] Issue 1: 编辑模型时显示脱敏密钥，保存后密钥不丢失
- [x] Issue 2: 自由输入题目后可在题库中查到
- [x] Issue 3: AI 分析过程无错误弹窗，可实时查看回复
