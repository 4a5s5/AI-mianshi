# Tasks: 题库管理增强与Docker部署

## Phase 1: 基础能力 - 多选/全选 (R2) ✅

### T1.1: 前端 - RepositoryView添加多选列 ✅
**文件**: `frontend/src/views/RepositoryView.vue`
**状态**: 已完成

### T1.2: 前端 - 批量操作工具栏 ✅
**文件**: `frontend/src/views/RepositoryView.vue`
**状态**: 已完成

---

## Phase 2: 多题型筛选 (R1) + 批量删除 (R3) ✅

### T2.1: 后端 - Question模型添加is_deleted字段 ✅
**文件**: `backend/app/models/question.py`
**状态**: 已完成

### T2.2: 后端 - 修改题目列表查询支持多题型+软删除过滤 ✅
**文件**: `backend/app/api/v1/routes_questions.py`
**状态**: 已完成

### T2.3: 后端 - 新增批量删除API ✅
**文件**: `backend/app/api/v1/routes_questions.py`
**状态**: 已完成

### T2.4: 前端 - 多题型筛选下拉框 ✅
**文件**: `frontend/src/views/RepositoryView.vue`
**状态**: 已完成

### T2.5: 前端 - 批量删除功能 ✅
**文件**: `frontend/src/api/questions.ts` + `frontend/src/views/RepositoryView.vue`
**状态**: 已完成

---

## Phase 3: 从题库练习 (R4) + 再次练习 (R5) ✅

### T3.1: 前端 - 从题库开始练习功能 ✅
**文件**: `frontend/src/views/RepositoryView.vue`
**状态**: 已完成

### T3.2: 前端 - SinglePracticeView支持路由参数 ✅
**文件**: `frontend/src/views/SinglePracticeView.vue`
**状态**: 已完成

### T3.3: 前端 - PaperPracticeView支持路由参数 ✅
**文件**: `frontend/src/views/PaperPracticeView.vue`
**状态**: 已完成

### T3.4: 前端 - PracticeResult添加retry事件 ✅
**文件**: `frontend/src/components/practice/PracticeResult.vue`
**状态**: 已完成

### T3.5: 前端 - SinglePracticeView实现retry ✅
**文件**: `frontend/src/views/SinglePracticeView.vue`
**状态**: 已完成

### T3.6: 前端 - PaperPracticeView实现retry ✅
**文件**: `frontend/src/views/PaperPracticeView.vue`
**状态**: 已完成

---

## Phase 4: Docker部署 (R6) ✅

### T4.1: 创建后端Dockerfile ✅
**文件**: `backend/Dockerfile`
**状态**: 已完成

### T4.2: 创建前端Dockerfile和nginx配置 ✅
**文件**: `frontend/Dockerfile` + `frontend/nginx.conf`
**状态**: 已完成

### T4.3: 创建docker-compose.yml ✅
**文件**: `docker-compose.yml`
**状态**: 已完成

### T4.4: 创建环境变量示例文件 ✅
**文件**: `.env.example`
**状态**: 已完成

### T4.5: 更新README添加Docker部署说明 ✅
**文件**: `README.md`
**状态**: 已完成

### T4.6: 集成测试
**状态**: 待用户在Docker环境中验证

---

## 实施总结

所有代码任务已完成。主要变更：

**后端**:
- `backend/app/models/question.py` - 新增is_deleted字段
- `backend/app/schemas/question.py` - 新增BatchDelete请求/响应模型
- `backend/app/api/v1/routes_questions.py` - 多题型筛选、软删除、批量删除API
- `backend/Dockerfile` - 新增

**前端**:
- `frontend/src/views/RepositoryView.vue` - 多选、批量删除、开始练习
- `frontend/src/views/SinglePracticeView.vue` - 路由参数支持、再次练习
- `frontend/src/views/PaperPracticeView.vue` - 路由参数支持、再次练习
- `frontend/src/components/practice/PracticeResult.vue` - retry事件
- `frontend/src/api/questions.ts` - batchDelete方法
- `frontend/Dockerfile` - 新增
- `frontend/nginx.conf` - 新增

**根目录**:
- `docker-compose.yml` - 新增
- `.env.example` - 新增
- `README.md` - Docker部署说明

**注意**: 首次运行需要执行数据库迁移添加is_deleted列，或删除旧数据库让SQLAlchemy自动创建新表结构。
