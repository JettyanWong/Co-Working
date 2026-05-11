# Coworking

团队协作平台 - 挂在云端的协同软件

## 技术栈

- **前端**: HTML + JS (CodeMirror + Quill + Yjs)
- **后端**: Flask + Flask-SocketIO + MySQL
- **实时协作**: Yjs (CRDT)
- **部署**: Docker

## 本地开发

### 方式一：Docker (推荐)

```bash
docker-compose up --build
```

访问 http://localhost

### 方式二：本地运行

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.local .env

# 运行
python run.py
```

访问 http://localhost:5000

## 功能

- [x] 用户注册/登录
- [x] 项目管理 + 任务认领
- [x] 文档管理 + Cell 编辑器
- [x] 文件上传/下载
- [x] 防爬虫（频率限制）
- [ ] Yjs 实时协作
- [ ] Cell 编辑器前端

## 目录结构

```
coworking/
├── docs/           # 文档
├── backend/        # Flask 后端
├── frontend/       # 前端静态文件
├── Dockerfile
└── docker-compose.yml
```
