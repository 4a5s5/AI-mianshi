# Design: 题库管理增强与Docker部署

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   Frontend (Nginx)  │    │      Backend (FastAPI)      │ │
│  │                     │    │                             │ │
│  │  - Static files     │───►│  - /api/v1/*               │ │
│  │  - SPA routing      │    │  - SQLite + aiosqlite      │ │
│  │  - API proxy /api   │    │  - gunicorn (workers=1)    │ │
│  │                     │    │                             │ │
│  │  Port: 80           │    │  Port: 8000                │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│                                      │                       │
│                              ┌───────▼───────┐              │
│                              │   Volumes     │              │
│                              │ - ./data      │              │
│                              │ - ./uploads   │              │
│                              └───────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### TD1: 多题型筛选 (R1)

**决策**: 修改现有`category`参数支持逗号分隔多值

```python
# backend/app/api/v1/routes_questions.py
@router.get("", response_model=QuestionListResponse)
async def list_questions(
    category: str = Query(None),  # 支持 "综合分析,组织协调"
    ...
):
    if category:
        categories = [c.strip() for c in category.split(",") if c.strip()]
        if len(categories) == 1:
            query = query.where(Question.category == categories[0])
        else:
            query = query.where(Question.category.in_(categories))
```

**理由**: 最小化API变更，向后兼容单值场景。

### TD2: 批量删除 (R3)

**决策**: 新增`POST /api/v1/questions/batch-delete`端点，软删除策略

```python
# 请求体
class BatchDeleteRequest(BaseModel):
    ids: list[int]

# 响应体
class BatchDeleteResponse(BaseModel):
    deleted_count: int
    blocked_ids: list[int]  # 有关联数据但已软删除的ID
```

**软删除实现**:
- Question表新增`is_deleted: bool = False`字段
- 删除操作设置`is_deleted = True`而非物理删除
- 列表查询默认过滤`is_deleted = False`
- Answer关联的Question被软删除后，历史记录显示"原题已删除"

**理由**: 保留历史数据完整性，用户答题记录不丢失。

### TD3: 从题库开始练习 (R4)

**决策**: 纯前端路由传参，无需后端变更

**单题模式**:
```typescript
// RepositoryView.vue
router.push({
  path: '/single-practice',
  query: { questionId: selectedIds[0].toString() }
})

// SinglePracticeView.vue
onMounted(async () => {
  const questionId = route.query.questionId
  if (questionId) {
    currentQuestion.value = await questionApi.get(Number(questionId))
    step.value = 'answer'  // 跳过选题
  }
})
```

**套卷模式**:
```typescript
// 弹出时限设置对话框后
router.push({
  path: '/paper-practice',
  query: {
    questionIds: selectedIds.join(','),
    timeLimit: timeLimit.toString()
  }
})

// PaperPracticeView.vue
onMounted(async () => {
  const questionIds = route.query.questionIds?.split(',')
  const timeLimit = Number(route.query.timeLimit) || 900
  if (questionIds?.length) {
    const questions = await Promise.all(
      questionIds.map(id => questionApi.get(Number(id)))
    )
    startPractice(questions, timeLimit)  // 复用现有逻辑
  }
})
```

**理由**: 完全复用现有练习逻辑，无需新增数据模型。

### TD4: 再次练习 (R5)

**决策**: 新增`retry`事件，区分`restart`（返回选题）和`retry`（重试同题）

**PracticeResult.vue**:
```vue
<el-button @click="emit('retry')">再次练习</el-button>
<el-button @click="emit('restart')">换题练习</el-button>
```

**SinglePracticeView.vue**:
```typescript
function handleRetry() {
  // 保留currentQuestion，只重置状态
  analysisResult.value = null
  isAnalyzing.value = false
  step.value = 'answer'
}
```

**PaperPracticeView.vue**:
```typescript
function handleRetry() {
  // 保留paperQuestions，重置计时器和答案
  paperTimer.reset(practiceStore.paperTimeLimit)
  paperTimer.start()
  paperAnswers.value = practiceStore.paperQuestions.map(q => ({
    questionId: q.id,
    transcript: '',
    duration: 0
  }))
  practiceStore.currentQuestionIndex = 0
  step.value = 'practice'
}
```

### TD5: Docker部署 (R6)

**Backend Dockerfile**:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY app ./app
EXPOSE 8000
CMD ["gunicorn", "app.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

**Frontend Dockerfile**:
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**docker-compose.yml**:
```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/interview.db
    networks:
      - ai-interview

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - ai-interview

networks:
  ai-interview:
    driver: bridge
```

**nginx.conf**:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

---

## Database Schema Changes

### Question表修改

```sql
ALTER TABLE questions ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
CREATE INDEX idx_questions_is_deleted ON questions(is_deleted);
```

---

## API Changes Summary

| 方法 | 路径 | 变更类型 | 说明 |
|------|------|----------|------|
| GET | /api/v1/questions | 修改 | category参数支持逗号分隔多值 |
| POST | /api/v1/questions/batch-delete | 新增 | 批量软删除题目 |
| GET | /api/v1/questions | 修改 | 默认过滤is_deleted=True的记录 |

---

## File Changes Summary

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| backend/app/models/question.py | 修改 | 新增is_deleted字段 |
| backend/app/api/v1/routes_questions.py | 修改 | 多值筛选+批量删除 |
| backend/app/schemas/question.py | 修改 | 新增BatchDelete相关schema |
| frontend/src/views/RepositoryView.vue | 修改 | 多选+批量操作+开始练习 |
| frontend/src/views/SinglePracticeView.vue | 修改 | 路由参数处理+retry |
| frontend/src/views/PaperPracticeView.vue | 修改 | 路由参数处理+retry |
| frontend/src/components/practice/PracticeResult.vue | 修改 | 新增retry事件 |
| frontend/src/api/questions.ts | 修改 | 新增batchDelete方法 |
| backend/Dockerfile | 新增 | 后端容器配置 |
| frontend/Dockerfile | 新增 | 前端容器配置 |
| frontend/nginx.conf | 新增 | Nginx配置 |
| docker-compose.yml | 新增 | 服务编排 |
| .env.example | 新增 | 环境变量示例 |
