# AI 面试助手 - 完整实施计划

> 天津公务员省考结构化面试 AI 练习助手 Web 应用

## 项目概述

### 技术栈
| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Pinia |
| 后端 | Python FastAPI + SQLite + BackgroundTasks |
| 录音 | Web Speech API + OpenAI Whisper API（可切换） |
| 部署 | Ubuntu 宝塔面板 + Nginx + Gunicorn |

### 核心功能
1. **单题练习**：随机抽取/手动输入 → 录音转文字 → 计时 → AI 分析打分
2. **套卷练习**：3-5 题倒计时练习 → 整套分析报告
3. **历史记录**：按日期分类 → 分数趋势图 → 多选 AI 综合分析
4. **题库管理**：上传 TXT/PDF → AI 解析导入 → 单题/套卷分类
5. **AI 配置**：双模型（作答分析 + 题库导入）→ 自定义 URL/Key/模型
6. **提示词系统**：6 类可编辑提示词

---

## 第一阶段：项目初始化与基础架构

### 1.1 后端目录结构
```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── core/
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # SQLite 连接
│   │   └── logging.py          # 日志配置
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── question.py
│   │   ├── paper.py
│   │   ├── answer.py
│   │   ├── analysis.py
│   │   ├── prompt.py
│   │   ├── model_config.py
│   │   ├── import_task.py
│   │   └── stats.py
│   ├── schemas/                # Pydantic 模型
│   ├── services/               # 业务逻辑
│   │   ├── ai_client.py        # AI 调用封装
│   │   ├── analyze_service.py
│   │   ├── import_service.py
│   │   └── speech_service.py   # Whisper 语音转写
│   ├── tasks/                  # 异步任务
│   │   ├── analyze_task.py
│   │   └── import_task.py
│   ├── api/v1/                 # 路由
│   │   ├── routes_questions.py
│   │   ├── routes_papers.py
│   │   ├── routes_answers.py
│   │   ├── routes_analysis.py
│   │   ├── routes_models.py
│   │   ├── routes_prompts.py
│   │   ├── routes_speech.py
│   │   └── routes_stats.py
│   └── utils/
├── requirements.txt
└── alembic/                    # 数据库迁移（可选）
```

### 1.2 前端目录结构
```
frontend/
├── src/
│   ├── api/                    # 接口定义
│   │   ├── request.ts          # Axios 封装
│   │   ├── questions.ts
│   │   ├── papers.ts
│   │   ├── answers.ts
│   │   ├── models.ts
│   │   └── prompts.ts
│   ├── assets/                 # 静态资源
│   ├── components/
│   │   ├── common/             # 通用组件
│   │   ├── business/           # 业务组件
│   │   │   ├── AudioRecorder.vue
│   │   │   ├── PracticeTimer.vue
│   │   │   ├── ScoreTrendChart.vue
│   │   │   └── AnalysisResult.vue
│   │   └── layout/
│   │       ├── AppSidebar.vue
│   │       └── MobileTabBar.vue
│   ├── composables/            # 组合式函数
│   │   ├── useRecorder.ts
│   │   ├── useTimer.ts
│   │   └── useResponsive.ts
│   ├── store/                  # Pinia
│   │   ├── app.ts              # 全局配置
│   │   ├── practice.ts         # 练习状态
│   │   └── history.ts          # 历史记录
│   ├── views/
│   │   ├── DashboardView.vue
│   │   ├── SinglePracticeView.vue
│   │   ├── MultiPracticeView.vue
│   │   ├── RepositoryView.vue
│   │   ├── HistoryView.vue
│   │   └── SettingsView.vue
│   ├── router/
│   └── utils/
├── index.html
├── vite.config.ts
└── package.json
```

---

## 第二阶段：数据库设计

### 2.1 核心表结构 (SQLite DDL)

```sql
PRAGMA foreign_keys = ON;

-- 题目表（单题）
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,           -- 题型（综合分析/组织协调/应急应变/人际关系等）
  content TEXT NOT NULL,            -- 题干
  analysis TEXT,                    -- 解析（可为空）
  reference_answer TEXT,            -- 参考答案（可为空）
  image_url TEXT,                   -- 思维导图图片（可为空）
  tags TEXT,                        -- 逗号分隔标签
  source TEXT,                      -- 来源（手工/导入）
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 套卷表
CREATE TABLE IF NOT EXISTS papers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,              -- 套卷名称（来自文档名）
  description TEXT,
  time_limit_seconds INTEGER,       -- 作答时限（秒）
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 套卷题目关联表
CREATE TABLE IF NOT EXISTS paper_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  sort_order INTEGER NOT NULL,
  FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT
);

-- 练习作答记录
CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL,               -- "single" | "paper"
  question_id INTEGER NOT NULL,
  paper_id INTEGER,                 -- 套卷模式时关联
  paper_session_id TEXT,            -- 套卷练习会话ID（同一次练习的多题共用）
  transcript TEXT,                  -- 转写文本
  audio_url TEXT,                   -- 音频存储地址（可选）
  duration_seconds INTEGER,         -- 作答时长
  started_at TEXT NOT NULL,
  finished_at TEXT,
  practice_date TEXT NOT NULL,      -- 练习日期 YYYY-MM-DD
  created_at TEXT NOT NULL,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
  FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE SET NULL
);

CREATE INDEX idx_answers_practice_date ON answers(practice_date);
CREATE INDEX idx_answers_mode ON answers(mode);

-- AI 分析结果
CREATE TABLE IF NOT EXISTS analysis_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  answer_id INTEGER NOT NULL,
  paper_session_id TEXT,            -- 套卷整体分析时使用
  analysis_type TEXT NOT NULL,      -- "single" | "paper" | "history_single" | "history_paper"
  score REAL,                       -- 总分
  score_details TEXT,               -- JSON：各维度得分
  feedback TEXT,                    -- AI 反馈内容
  model_answer TEXT,                -- 模范作答
  model_name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE
);

-- 题库导入任务
CREATE TABLE IF NOT EXISTS imports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,          -- txt/pdf
  import_type TEXT NOT NULL,        -- "single" | "paper"
  status TEXT NOT NULL,             -- pending/running/success/failed
  raw_text TEXT,
  result_summary TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- AI 模型配置
CREATE TABLE IF NOT EXISTS model_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  api_key TEXT NOT NULL,
  model_name TEXT NOT NULL,
  role TEXT NOT NULL,               -- "analyze" | "import"
  is_active INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 提示词
CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt_type TEXT NOT NULL UNIQUE, -- 6类提示词
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 语音转写配置
CREATE TABLE IF NOT EXISTS speech_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,           -- "web_speech" | "whisper"
  whisper_api_url TEXT,
  whisper_api_key TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);
```

---

## 第三阶段：API 路由设计

### 3.1 题库管理
| 方法 | 路由 | 说明 |
|------|------|------|
| POST | /api/v1/questions/import | 上传文件导入 |
| GET | /api/v1/questions | 分页查询题目 |
| POST | /api/v1/questions | 新增单题 |
| GET | /api/v1/questions/{id} | 题目详情 |
| PUT | /api/v1/questions/{id} | 更新题目 |
| DELETE | /api/v1/questions/{id} | 删除题目 |
| GET | /api/v1/questions/search | 搜索题目 |

### 3.2 套卷管理
| 方法 | 路由 | 说明 |
|------|------|------|
| POST | /api/v1/papers | 新建套卷 |
| GET | /api/v1/papers | 套卷列表 |
| GET | /api/v1/papers/{id} | 套卷详情（含题目） |
| PUT | /api/v1/papers/{id} | 更新套卷 |
| DELETE | /api/v1/papers/{id} | 删除套卷 |
| POST | /api/v1/papers/import | 上传文件导入套卷 |

### 3.3 作答与分析
| 方法 | 路由 | 说明 |
|------|------|------|
| POST | /api/v1/answers | 提交作答 |
| GET | /api/v1/answers/{id} | 作答详情 |
| POST | /api/v1/answers/{id}/analyze | 触发 AI 分析（单题） |
| POST | /api/v1/answers/paper-analyze | 触发套卷整体分析 |
| POST | /api/v1/answers/history-analyze | 触发历史综合分析 |
| GET | /api/v1/analysis/{answer_id} | 获取分析结果 |

### 3.4 历史记录与统计
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | /api/v1/history/single | 单题历史（按日期分组） |
| GET | /api/v1/history/paper | 套卷历史（按日期分组） |
| GET | /api/v1/stats/trends | 分数趋势数据 |

### 3.5 配置管理
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | /api/v1/models | 模型配置列表 |
| POST | /api/v1/models | 新增配置 |
| PUT | /api/v1/models/{id} | 更新配置 |
| DELETE | /api/v1/models/{id} | 删除配置 |
| POST | /api/v1/models/{id}/activate | 激活配置 |
| POST | /api/v1/models/fetch-models | 获取可用模型列表 |
| GET | /api/v1/prompts | 提示词列表 |
| PUT | /api/v1/prompts/{id} | 更新提示词 |
| GET | /api/v1/speech/config | 语音配置 |
| PUT | /api/v1/speech/config | 更新语音配置 |
| POST | /api/v1/speech/transcribe | Whisper 转写 |

---

## 第四阶段：前端页面路由

```typescript
// router/index.ts
const routes = [
  { path: '/', name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/practice/single', name: 'SinglePractice', component: () => import('@/views/SinglePracticeView.vue') },
  { path: '/practice/paper', name: 'PaperPractice', component: () => import('@/views/PaperPracticeView.vue') },
  { path: '/repository', name: 'Repository', component: () => import('@/views/RepositoryView.vue') },
  { path: '/history', name: 'History', component: () => import('@/views/HistoryView.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/views/SettingsView.vue') },
]
```

---

## 第五阶段：核心组件设计

### 5.1 录音组件 (AudioRecorder.vue)
- Props: `disabled`, `maxDuration`
- Emits: `start`, `stop`, `transcript`, `error`
- 功能：
  - 支持 Web Speech API 实时转写
  - 支持 Whisper API 录音后转写
  - 麦克风权限检测
  - 音量可视化（波形动画）
  - 录音状态指示

### 5.2 计时器组件 (PracticeTimer.vue)
- Props: `mode` (count-up/count-down), `duration`, `warning`
- Emits: `tick`, `timeout`, `warning`
- 功能：
  - 正计时（单题模式）
  - 倒计时（套卷模式）
  - 最后 30 秒警告
  - 暂停/继续

### 5.3 趋势图组件 (ScoreTrendChart.vue)
- Props: `data`, `type` (single/paper)
- 功能：
  - 分数变化折线图
  - 点击跳转详情
  - 响应式缩放

### 5.4 分析结果组件 (AnalysisResult.vue)
- Props: `analysis`
- 功能：
  - 各维度评分展示
  - 亮点/改进点高亮
  - 模范作答折叠展示

---

## 第六阶段：提示词模板

### 6.1 作答分析提示词
```
你是一位资深的公务员面试考官，精通天津省考结构化面试评分规则。请根据以下评分细则对考生的作答进行全面分析：

## 评分细则
1. 语言表达 (权重15分)：口齿清晰度、用词准确性、逻辑条理性
2. 综合分析能力 (权重20分)：问题剖析深度、根源认识、对策可行性
3. 应变能力 (权重20分)：情绪稳定性、反应敏捷度、解决方案有效性
4. 人际交往能力 (权重15分)：合作意识、沟通有效性、原则性
5. 计划组织协调能力 (权重20分)：预见性、计划科学性、资源配置合理性
6. 举止仪表 (权重10分)：（基于文字作答无法评估，给予基础分6分）

## 作答原则
- 问啥答啥，直截了当
- 回到生活工作中真正解决问题
- 纵向分层：时间顺序、主体顺序
- 横向展开：连接词+观点+分析+解决
- 劝说五法：动之以情、晓之以理、诱之以利、避之以害、绳之以法

## 题目
{question}

## 考生作答
{answer}

## 作答时长
{duration}秒

请按以下格式输出：
1. **总体评分**：X/100 分
2. **各维度得分**：
   - 语言表达：X/15
   - 综合分析：X/20
   - 应变能力：X/20
   - 人际交往：X/15
   - 计划组织：X/20
   - 举止仪表：6/10（默认）
3. **亮点与保持**：（2-3条）
4. **不足与改进**：（2-3条）
5. **题目分析**：分析本题考查要点和作答逻辑
6. **模范作答**：根据作答原则生成一份高分参考答案
```

### 6.2 历史作答分析提示词
```
你是一位资深的公务员面试教练。现在需要对考生的多次练习记录进行综合分析。

## 练习记录（按时间顺序）
{history_records}

请按以下格式输出：
1. **整体进步趋势**：分析分数变化走势
2. **作答习惯总结**：识别考生的固定表达模式和思维方式
3. **持续性不足**：指出多次出现的问题
4. **进步的点**：对比早期和近期，指出明显改善的方面
5. **退步的点**：如有，指出下滑的方面
6. **针对性练习建议**：给出接下来应该重点练习的题型和方向
```

### 6.3 套卷作答分析提示词
```
在作答分析的基础上，增加：
- 各题作答时长分析
- 时间分配是否合理
- 整套试卷的节奏把控
- 各题之间的逻辑一致性
```

### 6.4 套卷历史作答分析提示词
```
在历史作答分析的基础上，增加：
- 套卷作答时间分配规律
- 各题型得分分布
- 整体把控能力的变化趋势
```

### 6.5 单题题库导入提示词
```
请从以下文档内容中提取面试题目信息：

{document_content}

请按 JSON 格式输出，每道题包含：
- question: 题目内容
- category: 题型（综合分析/组织协调/应急应变/人际关系/自我认知）
- analysis: 解析（如有）
- reference_answer: 参考答案（如有）
```

### 6.6 套卷题库导入提示词
```
请从以下文档内容中提取套卷信息：

文档名称：{file_name}
{document_content}

请按 JSON 格式输出：
- paper_title: 套卷名称（从文档名提取）
- questions: 题目数组，每题包含 question, category, analysis, reference_answer
```

---

## 第七阶段：实施顺序

### Phase 1: 基础框架（预计工作量：后端+前端骨架）
1. 后端项目初始化 + 数据库创建
2. 前端项目初始化 + 路由配置
3. API 接口封装 + 基础布局组件

### Phase 2: 核心功能（AI 配置 + 单题练习）
1. AI 模型配置管理
2. 提示词管理
3. 单题练习（不含录音）
4. AI 分析功能

### Phase 3: 录音与语音转写
1. Web Speech API 集成
2. Whisper API 集成
3. 录音组件完善

### Phase 4: 套卷练习
1. 套卷管理
2. 套卷练习流程
3. 套卷分析

### Phase 5: 历史记录与统计
1. 历史记录查询
2. 分数趋势图
3. 历史综合分析

### Phase 6: 题库管理
1. 文件上传
2. AI 解析导入
3. 题库搜索

### Phase 7: 优化与部署
1. 响应式适配优化
2. 性能优化
3. 宝塔部署配置

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| SQLite 并发锁 | 分析结果拆表存储，避免大字段更新 |
| AI 调用超时 | 重试机制 + 超时控制 + 前端 loading 状态 |
| PDF 解析不准确 | 保留原文 + 人工校正入口 |
| 移动端录音兼容性 | Web Speech API 降级为手动输入 |
| 低配服务器性能 | 异步任务 + 静态资源 CDN + 数据库索引优化 |
