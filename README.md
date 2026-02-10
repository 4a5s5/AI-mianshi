# AI面试助手 - 部署指南

## 项目结构

```
ai面试助手/
├── backend/           # FastAPI 后端
│   ├── app/           # 应用代码
│   ├── data/          # SQLite 数据库（自动创建）
│   ├── uploads/       # 上传文件
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 本地开发

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 宝塔面板部署

### 1. 后端部署

1. 在宝塔面板创建 Python 项目
2. 上传 `backend` 目录到服务器
3. 设置 Python 版本 >= 3.10
4. 安装依赖：`pip install -r requirements.txt`
5. 配置启动命令：
   ```bash
   gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```
6. 设置自启动

### 2. 前端构建

```bash
cd frontend
npm run build
```

生成的 `dist` 目录即为静态文件。

### 3. Nginx 配置

在宝塔面板中配置 Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /www/wwwroot/ai-interview/frontend/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;  # AI 分析可能需要较长时间
    }
}
```

### 4. HTTPS 配置

语音录音功能需要 HTTPS。在宝塔面板中：
1. 申请 SSL 证书（可使用 Let's Encrypt 免费证书）
2. 开启强制 HTTPS

## 首次使用

1. 访问 `/settings`，配置 AI 模型
2. 填写 API 地址、密钥，获取并选择模型
3. 激活作答分析模型
4. 返回首页开始练习

## 注意事项

- 录音功能需要 HTTPS 环境
- Chrome/Edge 浏览器对 Web Speech API 支持最佳
- 服务器需要能访问外部 AI API
- SQLite 数据库文件在 `backend/data/interview.db`

## Docker 部署

### 快速开始

1. 确保服务器已安装 Docker 和 Docker Compose
2. 克隆项目并进入目录
3. 启动服务：
   ```bash
   docker compose up -d --build
   ```
4. 访问 http://服务器IP

### 数据持久化

数据存储在以下目录（需确保Docker有写入权限）：
- `./data/` - SQLite数据库
- `./uploads/` - 上传的文件

### 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 重新构建并启动
docker compose up -d --build

# 查看运行状态
docker compose ps
```

### 自定义端口

如需更改前端端口，修改 `docker-compose.yml` 中的端口映射：
```yaml
frontend:
  ports:
    - "8080:80"  # 改为8080端口
```

### HTTPS 配置

生产环境建议在 Docker 外层使用 Nginx 或 Traefik 处理 HTTPS：
1. 修改 `docker-compose.yml` 将前端端口改为非80端口（如8080）
2. 在宿主机 Nginx 配置 SSL 证书并反向代理到 Docker 容器
