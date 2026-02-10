# UX Improvements V2 - 技术规格

## 约束决策记录

| # | 决策点 | 决策结果 |
|---|--------|----------|
| 1 | API 密钥脱敏规则 | 前 3 后 4 位，不足 8 位全掩码 |
| 2 | SSE 端点路径 | `GET /answers/{id}/analysis/stream` |
| 3 | SSE 连接中断处理 | 后台继续分析并写入数据库 |
| 4 | 同一 answer_id 多次 SSE | 已有结果直接返回，分析中拒绝新连接 |
| 5 | QuestionCreate 最小字段 | `content` 必填，`category` 默认"自定义" |
| 6 | 自由输入题目去重 | 不去重，允许重复内容 |
| 7 | SSE 超时 | 120 秒最大时长 |
| 8 | 旧轮询接口 | 保留兼容，SSE 为优先方案 |

---

## Issue 1: API 密钥持久化

### 需求规格

**R1.1** 后端返回脱敏密钥
- `ModelConfigResponse` 新增 `api_key_masked: str | None` 字段
- 脱敏规则：`sk-abc...xyz`（前 3 后 4，中间 `...`）
- 长度 < 8 时返回 `***`
- 空值或 None 时返回 `None`

**R1.2** 前端编辑显示
- 编辑时 placeholder 显示脱敏值
- `api_key` 输入框初始为空
- 提示文案："留空则保持原密钥"

### PBT 属性

| 属性 | 不变式 | 伪造策略 |
|------|--------|----------|
| 脱敏长度 | `len(masked) <= len(original)` | 生成各种长度密钥测试 |
| 前缀保留 | `masked.startswith(original[:3])` 当 `len >= 8` | 边界测试 7/8/9 位密钥 |
| 空值处理 | `masked is None` 当 `original is None or ""` | 传入空字符串和 None |

---

## Issue 2: 自由输入题目自动入库

### 需求规格

**R2.1** 题目创建流程
- `handleCustom` 变为异步函数
- 调用 `POST /questions` 创建题目
- 最小字段：`{ content, category: "自定义" }`
- 获取返回的真实 ID 赋给 `currentQuestion`

**R2.2** 错误处理
- 创建失败时显示错误提示
- 阻止进入作答步骤
- 允许用户重新点击"开始练习"

### PBT 属性

| 属性 | 不变式 | 伪造策略 |
|------|--------|----------|
| ID 有效性 | `currentQuestion.id > 0` 进入作答步骤 | 模拟 API 失败返回 id=0 |
| 题库可查 | 题目创建后可通过列表 API 查到 | 创建后立即查询验证 |

---

## Issue 3: SSE 流式输出

### 需求规格

**R3.1** 后端 SSE 端点
- 路径：`GET /answers/{id}/analysis/stream`
- Content-Type: `text/event-stream`
- 事件格式：
  ```
  event: token
  data: {"content": "增量文本"}

  event: done
  data: {"score": 85, "full_content": "完整分析"}

  event: error
  data: {"message": "错误信息"}
  ```

**R3.2** 状态处理逻辑
- 已有 AnalysisResult：直接发送 `done` 事件 + 结果
- 分析中（锁定状态）：返回 409 Conflict
- 无结果：开始分析并流式输出

**R3.3** 连接中断处理
- 捕获 `asyncio.CancelledError`
- 继续后台分析直到完成
- 将结果写入数据库

**R3.4** 前端实现
- 使用 `fetch` + `ReadableStream`
- 引入 `isStreaming` 状态位
- 增量更新 `analysisResult.content`
- 完成后更新完整结果

**R3.5** 错误弹窗修复
- 修改 `request.ts` 拦截器
- 支持 `_silent` 配置项跳过全局错误提示
- 或使用独立 fetch 不经过 axios

### PBT 属性

| 属性 | 不变式 | 伪造策略 |
|------|--------|----------|
| 最终一致性 | SSE 完成后 DB 必有记录 | 断开连接后检查数据库 |
| 幂等性 | 重复请求已完成分析返回相同结果 | 连续调用两次比较响应 |
| 超时保护 | 120s 后连接必须关闭 | 模拟慢速 AI 响应 |

---

## Issue 4: 移动端题库入口

### 需求规格

**R4.1** 导航添加
- 在 `mobile-tabbar` 添加第 5 个入口
- 位置：练习和记录之间
- 路径：`/repository`
- 图标：`Folder`
- 文案：`题库`

**R4.2** 样式适配
- 5 个 Tab 等宽排列
- 使用 `flex: 1` 确保均分
- 最小宽度约束防止文字重叠
- 点击热区符合触屏规范（44px）

### PBT 属性

| 属性 | 不变式 | 伪造策略 |
|------|--------|----------|
| 可见性 | 移动端（宽度<768px）必显示题库入口 | 不同屏幕宽度测试 |
| 可用性 | 点击后正确导航到 /repository | E2E 测试点击行为 |

---

## SSE 协议详细定义

### 事件类型

```typescript
// token 事件 - 增量内容
interface TokenEvent {
  event: 'token'
  data: { content: string }
}

// done 事件 - 分析完成
interface DoneEvent {
  event: 'done'
  data: {
    score: number | null
    full_content: string
    analysis_id: number
  }
}

// error 事件 - 错误
interface ErrorEvent {
  event: 'error'
  data: { message: string }
}
```

### 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 开始流式输出 |
| 404 | Answer 不存在 |
| 409 | 分析正在进行中 |
| 500 | 服务器错误 |

### 超时规则

- 连接最大时长：120 秒
- 心跳间隔：每 15 秒发送 `:keepalive\n\n`
- AI 响应超时：60 秒无 token 则发送 error 并关闭
