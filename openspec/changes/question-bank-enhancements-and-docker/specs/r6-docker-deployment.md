# Spec: R6 Docker部署

## Requirement

支持通过Docker Compose在云服务器上一键部署应用，前端通过Nginx托管并反向代理后端API。

## Scenarios

### S6.1: 首次部署

**Given**: 服务器已安装Docker和Docker Compose
**When**: 执行`docker compose up -d --build`
**Then**:
  - 后端容器构建并启动，监听8000端口
  - 前端容器构建并启动，监听80端口
  - 数据卷`./data`和`./uploads`自动创建

### S6.2: 访问应用

**Given**: 容器正常运行
**When**: 浏览器访问`http://服务器IP`
**Then**: 显示AI面试助手前端页面

### S6.3: API调用

**Given**: 容器正常运行
**When**: 前端调用`/api/v1/questions`
**Then**: Nginx反向代理到后端容器，返回题目列表

### S6.4: 数据持久化

**Given**: 用户添加了题目并进行了练习
**When**: 执行`docker compose down && docker compose up -d`
**Then**: 重启后数据仍然存在

### S6.5: 停止服务

**Given**: 容器正常运行
**When**: 执行`docker compose down`
**Then**: 所有容器停止，数据卷保留

## PBT Properties

### P6.1: 服务健康性

```
docker compose up -d
⟹ curl http://localhost/api/v1/questions returns 200
   ∧ curl http://localhost returns 200
```

**Falsification**: 任一端点返回非200状态

### P6.2: 数据卷持久性

```
createQuestion(q)
docker compose down
docker compose up -d
⟹ getQuestion(q.id) returns q
```

**Falsification**: 重启后数据丢失

### P6.3: 网络隔离性

```
docker compose network
⟹ backend:8000 仅可从frontend容器访问
   ∧ 宿主机仅暴露80端口
```

**Falsification**: 外部可直接访问backend:8000

## Implementation Constraints

### 文件结构

```
/
├── docker-compose.yml
├── .env.example
├── backend/
│   └── Dockerfile
└── frontend/
    ├── Dockerfile
    └── nginx.conf
```

### 环境变量

```env
# .env.example
DATABASE_URL=sqlite+aiosqlite:///./data/interview.db
CORS_ORIGINS=*
```

### 资源限制建议

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
  frontend:
    deploy:
      resources:
        limits:
          memory: 128M
```
