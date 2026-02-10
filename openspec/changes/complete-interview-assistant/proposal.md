# AI面试助手 - 功能完善与Bug修复提案

> 完成未实现功能，修复已发现问题，提升代码质量

## 背景与目标

AI面试助手是一款天津公务员省考结构化面试练习 Web 应用，采用 Vue 3 + FastAPI 技术栈。项目核心功能框架已搭建完成，但存在以下问题需要解决：

1. **未完成的模块化重构**：前端组件未按计划拆分
2. **后端数据校验缺失**：多个 API 缺少输入验证
3. **错误处理不完善**：AI 调用和业务异常未妥善处理
4. **代码质量问题**：TypeScript 类型松散、资源清理缺失

---

## 约束集合 (Constraint Sets)

### 硬约束 (Hard Constraints)

| ID | 约束 | 来源 |
|----|------|------|
| HC-1 | 不得破坏现有 API 接口契约 | 兼容性要求 |
| HC-2 | 后端必须保持 Python 3.10+ 兼容 | 技术栈限制 |
| HC-3 | 前端必须保持 Vue 3 Composition API 风格 | 技术栈限制 |
| HC-4 | 数据库结构修改需向后兼容 | 数据安全 |
| HC-5 | AI 调用必须有超时控制（≤60秒） | 用户体验 |

### 软约束 (Soft Constraints)

| ID | 约束 | 来源 |
|----|------|------|
| SC-1 | 组件拆分应遵循原计划目录结构 | 设计文档 |
| SC-2 | 优先修复 major/critical 级别问题 | 风险管理 |
| SC-3 | 保持代码风格一致性 | 可维护性 |

---

## 发现的问题

### 后端问题 (Codex 分析)

#### Bug - Major 级别

| 位置 | 问题描述 |
|------|----------|
| `routes_answers.py:29` | 创建作答未校验 question_id 存在性、mode 合法性，可能触发外键错误返回 500 |
| `routes_papers.py:54` | 创建套卷未校验题目存在性，可能触发外键错误导致事务失败 |
| `models/analysis.py:11` | answer_id 未加唯一约束，但 ORM 设为 uselist=False，可能抛 MultipleResultsFound |
| `services/ai_client.py:18` | AI 调用缺少超时/异常处理，网络错误会直接 500 |

#### Bug - Minor 级别

| 位置 | 问题描述 |
|------|----------|
| `routes_import.py:20` | 文件后缀判断大小写敏感，.TXT/.PDF 会被拒绝 |
| `routes_answers.py:159` | 历史分析未捕获 ValueError 异常 |
| `routes_answers.py:203` | 套卷分析未捕获 ValueError 异常 |
| `routes_speech.py:38` | 语音配置更新使用查询参数而非 JSON body |

### 前端问题 (Gemini 分析)

#### 未完成功能 - High 优先级

| 位置 | 问题描述 |
|------|----------|
| `components/` 目录 | 计划的 business/common/layout 目录均为空，AudioRecorder/PracticeTimer 等组件未拆分 |

#### 未完成功能 - Medium 优先级

| 位置 | 问题描述 |
|------|----------|
| `views/DashboardView.vue` | ECharts 实例未在组件卸载时销毁，存在内存泄漏风险 |

#### 代码质量问题

| 位置 | 问题描述 |
|------|----------|
| `views/DashboardView.vue:102` | ECharts formatter 使用 any 类型 |
| `views/SettingsView.vue:301` | updateData 对象使用 any 类型 |
| `composables/useRecorder.ts:153` | catch 块使用 any 类型 |
| `views/SinglePracticeView.vue` | 视图文件过大（496行），混合多种逻辑 |

---

## 需求定义

### Requirement 1: 后端输入验证强化

**目标**：确保所有 API 输入经过校验，返回明确的错误信息

#### Scenario 1.1: 创建作答时题目不存在
- Given: 用户提交作答，question_id 不存在于数据库
- When: 调用 POST /api/v1/answers
- Then: 返�� 404 状态码，消息为 "题目不存在"

#### Scenario 1.2: 创建套卷时题目不存在
- Given: 用户创建套卷，question_ids 中包含不存在的题目
- When: 调用 POST /api/v1/papers
- Then: 返回 400 状态码，消息指明哪些题目不存在

#### Scenario 1.3: 作答 mode 不合法
- Given: 用户提交作答，mode 不是 "single" 或 "paper"
- When: 调用 POST /api/v1/answers
- Then: 返回 400 状态码，消息为 "mode 必须为 single 或 paper"

### Requirement 2: AI 调用健壮性

**目标**：AI 调用有超时控制和异常处理

#### Scenario 2.1: AI 调用超时
- Given: AI 服务响应时间超过 60 秒
- When: 执行 AI 分析任务
- Then: 终止请求，返回超时错误

#### Scenario 2.2: AI 服务不可用
- Given: AI 服务 base_url 无法连接
- When: 执行 AI 分析任务
- Then: 返回明确的错误信息 "AI 服务连接失败"

#### Scenario 2.3: 未配置 AI 模型
- Given: 用户未配置激活的分析模型
- When: 触发 AI 分析
- Then: 返回 400 状态码，消息为 "请先配置并激活分析模型"

### Requirement 3: 分析结果数据完整性

**目标**：确保每个作答最多只有一条分析结果

#### Scenario 3.1: 防止重复分析
- Given: 作答已有分析结果
- When: 再次触发分析
- Then: 返回 400 状态码，消息为 "已有分析结果"

### Requirement 4: 前端资源管理

**目标**：正确管理 ECharts 等资源的生命周期

#### Scenario 4.1: 组件卸载时清理资源
- Given: DashboardView 组件已挂载并初始化了 ECharts
- When: 用户导航离开该页面
- Then: ECharts 实例被正确销毁

### Requirement 5: 前端类型安全

**目标**：消除不必要的 any 类型使用

#### Scenario 5.1: API 响应类型化
- Given: 前端调用后端 API
- When: 处理响应数据
- Then: 所有响应数据有明确的 TypeScript 类型定义

---

## 成功判据

1. [ ] 所有 major 级别后端 Bug 已修复
2. [ ] AI 调用有 60 秒超时控制
3. [ ] 前端 ECharts 资源在组件卸载时正确销毁
4. [ ] 项目代码中不存在 `: any` 或 `as any`（node_modules 除外）
5. [ ] 所有 API 输入验证测试通过
6. [ ] 后端服务可正常启动并通过健康检查

---

## 实施优先级

### P0 - 必须修复（阻塞性问题）
1. 后端输入验证强化（routes_answers.py, routes_papers.py）
2. AI 调用超时与异常处理（ai_client.py）

### P1 - 应该修复（用户体验问题）
1. 文件后缀大小写判断（routes_import.py）
2. 业务异常捕获（routes_answers.py 159/203 行）
3. ECharts 资源清理（DashboardView.vue）

### P2 - 可以改进（代码质量）
1. TypeScript any 类型替换
2. 语音配置 API 风格统一
3. 组件拆分重构（根据时间决定）

---

## 影响范围

### 需修改文件

**后端**：
- `backend/app/api/v1/routes_answers.py`
- `backend/app/api/v1/routes_papers.py`
- `backend/app/api/v1/routes_import.py`
- `backend/app/api/v1/routes_speech.py`
- `backend/app/services/ai_client.py`
- `backend/app/models/analysis.py`

**前端**：
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/SettingsView.vue`
- `frontend/src/views/RepositoryView.vue`
- `frontend/src/composables/useRecorder.ts`

### 不涉及修改

- 数据库表结构（仅添加约束，无破坏性变更）
- API 接口路径（保持兼容）
- 第三方依赖版本
