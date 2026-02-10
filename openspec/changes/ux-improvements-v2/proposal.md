# UX Improvements V2 - 用户体验改进

> 修复 4 个用户反馈的关键问题

## Context (背景)

用户在使用 AI 面试助手过程中反馈了以下 4 个问题，影响日常使用体验：

1. API 密钥编辑时消失，需要反复输入
2. 自由输入题目不会自动加入题库
3. AI 回复无流式输出，等待期间持续报错弹窗
4. 移动端题库管理入口缺失

---

## 约束集合 (Constraint Sets)

### Issue 1: API 密钥持久化

**Hard Constraints:**
- 后端 `ModelConfigResponse` schema 不包含 `api_key` 字段（安全设计）
- 前端 `editModel` 函数显式将 `api_key` 重置为空字符串
- API Key 当前仅支持 Write-only 模式

**Soft Constraints:**
- 用户希望编辑时能看到密钥已存在的提示
- 可选择本地存储密钥以避免服务器传输

**Solution Direction:**
- 方案 A: 后端返回 `has_api_key: bool` 标识，前端显示占位符 `******`
- 方案 B: 使用 localStorage 存储密钥（纯前端方案，但需考虑安全）
- **推荐方案 A**：后端增加脱敏返回 `api_key_masked: "sk-***xyz"`

**Affected Files:**
- `backend/app/schemas/config.py` - ModelConfigResponse
- `backend/app/api/v1/routes_models.py` - list_models, get_model
- `frontend/src/views/SettingsView.vue` - editModel, saveModel

---

### Issue 2: 自由输入题目自动入库

**Hard Constraints:**
- 当前 `handleCustom` 创建临时 Question 对象 (id: 0)
- 后端 `create_answer` 会验证 `question_id` 存在性，id=0 会导致 404
- 题目和答案需分离存储

**Current Flow:**
1. 用户输入自定义题目 → `handleCustom` 创建 `{ id: 0, content: ... }`
2. 练习完成 → `handleComplete` 调用 `answerApi.create({ question_id: 0 })`
3. 后端验证失败 → 404 题目不存在

**Solution Direction:**
- 自定义题目时，先调用 `questionApi.create` 创建题目获取真实 ID
- 再用真实 ID 继续后续流程
- 需添加 loading 状态提示"正在保存题目..."

**Affected Files:**
- `frontend/src/views/SinglePracticeView.vue` - handleCustom, handleComplete
- `frontend/src/api/questions.ts` - 确认 create 接口

---

### Issue 3: AI 回复流式输出

**Hard Constraints:**
- 当前使用后台任务 `BackgroundTasks` + 前端轮询 (1秒间隔，最多60次)
- `request.ts` 拦截器对所有错误调用 `ElMessage.error`
- 轮询期间 404 会触发错误弹窗

**Root Cause:**
- 轮询逻辑捕获 404 后虽然继续重试，但 axios 拦截器已经先触发了 `ElMessage.error`
- 这导致等待期间持续弹出错误提示

**Solution Direction:**
- **短期方案**：修改轮询请求，跳过全局错误拦截器（使用独立 axios 实例或 config 标记）
- **长期方案**：实现 SSE 流式输出
  - 后端: 使用 `StreamingResponse` + `text/event-stream`
  - 前端: 使用 `EventSource` 或 `fetch` + `ReadableStream`

**Affected Files:**
- `frontend/src/api/request.ts` - 错误拦截器
- `frontend/src/views/SinglePracticeView.vue` - pollAnalysisResult
- `backend/app/api/v1/routes_answers.py` - 新增 SSE 端点 (长期)
- `backend/app/services/ai_client.py` - stream=True (长期)

---

### Issue 4: 移动端题库管理入口缺失

**Hard Constraints:**
- 移动端底部导航栏仅有 4 个入口：首页、练习、记录、设置
- PC 端侧边栏有 5 个入口，包含"题库管理"
- 底部导航栏空间有限，通常 4-5 个为宜

**Current Implementation (App.vue:47-64):**
```html
<nav v-if="isMobile" class="mobile-tabbar">
  <router-link to="/">首页</router-link>
  <router-link to="/practice/single">练习</router-link>
  <router-link to="/history">记录</router-link>
  <router-link to="/settings">设置</router-link>
</nav>
```

**Solution Direction:**
- 方案 A: 直接添加第 5 个导航项"题库"
- 方案 B: 在"设置"页面添加"题库管理"入口
- 方案 C: 添加"更多"按钮，展开显示更多功能
- **推荐方案 A**：5 个导航项在底部栏仍可接受

**Affected Files:**
- `frontend/src/App.vue` - mobile-tabbar 区域

---

## Requirements (需求规格)

### R1: API 密钥编辑体验优化
- **Scenario**: 用户点击"编辑"已配置的模型
- **Expected**: 密钥输入框显示脱敏值 `sk-***xyz`，提示"留空则保持原密钥"
- **Acceptance**: 编辑保存后密钥不丢失

### R2: 自由输入题目自动入库
- **Scenario**: 用户输入题库中不存在的题目
- **Expected**: 系统自动将题目（不含答案）添加到题库，然后开始练习
- **Acceptance**: 题库中能查询到该题目

### R3: AI 回复流式输出 (分阶段)
- **Phase 1**: 修复等待期间的错误弹窗问题
- **Phase 2**: 实现流式输出，用户可实时查看回复内容
- **Acceptance**: 等待期间无错误弹窗；流式输出实时可见

### R4: 移动端题库管理入口
- **Scenario**: 用户在手机浏览器打开应用
- **Expected**: 底部导航栏显示"题库"入口
- **Acceptance**: 点击可正常进入题库管理页面

---

## Success Criteria (验收标准)

| # | 需求 | 验收条件 |
|---|------|----------|
| 1 | API 密钥持久化 | 编辑模型后密钥不丢失，显示脱敏占位符 |
| 2 | 题目自动入库 | 自由输入题目后可在题库管理中查到 |
| 3 | 流式输出 Phase1 | 等待 AI 回复期间无错误弹窗 |
| 4 | 移动端题库入口 | 手机端底部导航显示题库并可正常使用 |

---

## Implementation Priority (实施优先级)

1. **Issue 4** (移动端题库入口) - 改动最小，影响最大
2. **Issue 1** (API 密钥持久化) - 用户痛点明显
3. **Issue 3 Phase1** (修复错误弹窗) - 体验问题
4. **Issue 2** (题目自动入库) - 功能增强
5. **Issue 3 Phase2** (流式输出) - 可后续迭代

---

## Open Questions

1. ~~API 密钥存储位置？~~ → 决定：后端返回脱敏值，不使用 localStorage
2. ~~移动端导航数量？~~ → 决定：增加到 5 个
3. ~~流式输出 Phase2 是否在本次实施？~~ → 决定：本次完整实施 SSE 流式输出

---

## 决策记录

| 日期 | 问题 | 决策 |
|------|------|------|
| 2026-02-06 | 流式输出范围 | 完整实施 SSE 流式输出，包括修复弹窗和实时显示 |
