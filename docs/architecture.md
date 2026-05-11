# Coworking 系统架构设计

**版本**：V0.1
**日期**：2026-05-10
**状态**：初稿

---

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│   Browser (HTML/JS)                                         │
│   ├── CodeMirror (代码 Cell)                                │
│   ├── Quill (文本 Cell)                                     │
│   └── Yjs (实时协作 CRDT)                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                        服务端层                              │
│   Flask Application                                        │
│   ├── /auth/*        (用户认证)                             │
│   ├── /api/users/*   (人员管理)                             │
│   ├── /api/projects/* (项目管理)                             │
│   ├── /api/docs/*     (文档管理)                             │
│   └── /api/files/*    (文件管理)                             │
│   Flask-SocketIO (WebSocket 实时协作)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                        数据层                               │
│   MySQL                                                  │
│   └──users, projects, tasks, documents, files, etc.        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 数据库 ERD

### 2.1 用户与认证

```
users
├── id          (PK, INT, AUTO_INCREMENT)
├── username    (VARCHAR(50), UNIQUE, NOT NULL)
├── email       (VARCHAR(100), UNIQUE, NOT NULL)
├── password    (VARCHAR(255), NOT NULL)  # bcrypt hash
├── role        (ENUM: 'admin', 'member', DEFAULT: 'member')
├── created_at  (DATETIME)
└── updated_at  (DATETIME)
```

### 2.2 项目与任务

```
projects
├── id           (PK, INT, AUTO_INCREMENT)
├── name         (VARCHAR(100), NOT NULL)
├── description  (TEXT)
├── owner_id     (FK → users.id)
├── created_at   (DATETIME)
└── updated_at   (DATETIME)

project_members
├── id           (PK, INT, AUTO_INCREMENT)
├── project_id   (FK → projects.id)
├── user_id      (FK → users.id)
├── role         (ENUM: 'owner', 'member')
└── joined_at    (DATETIME)

tasks
├── id           (PK, INT, AUTO_INCREMENT)
├── project_id   (FK → projects.id)
├── title        (VARCHAR(200), NOT NULL)
├── description  (TEXT)
├── status       (ENUM: 'pending', 'in_progress', 'completed')
├── assignee_id  (FK → users.id, NULLABLE)
├── created_by   (FK → users.id)
├── created_at   (DATETIME)
└── updated_at   (DATETIME)
```

### 2.3 文档管理

```
documents
├── id           (PK, INT, AUTO_INCREMENT)
├── project_id   (FK → projects.id, NULLABLE)  # 可独立于项目
├── title        (VARCHAR(200), NOT NULL)
├── content      (LONGTEXT)  # Yjs CRDT binary
├── owner_id     (FK → users.id)
├── created_at   (DATETIME)
└── updated_at   (DATETIME)

document_cells
├── id           (PK, INT, AUTO_INCREMENT)
├── document_id  (FK → documents.id)
├── cell_type    (ENUM: 'code', 'text')
├── cell_order   (INT)  # 排序
├── content      (TEXT)
└── created_at   (DATETIME)
```

### 2.4 文件管理

```
files
├── id           (PK, INT, AUTO_INCREMENT)
├── project_id   (FK → projects.id, NULLABLE)
├── filename     (VARCHAR(255), NOT NULL)
├── filepath     (VARCHAR(500), NOT NULL)  # 存储路径
├── size         (INT)  # bytes
├── uploader_id  (FK → users.id)
├── created_at   (DATETIME)
└── updated_at   (DATETIME)
```

### 2.5 ERD 关系图

```
users ──┬── created ── projects
        ├── owned_documents
        ├── uploaded_files
        └── assigned_tasks

users ── project_members ── projects ──┬── tasks
                                        ├── documents
                                        └── files
```

---

## 3. API 接口设计

### 3.1 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/logout` | 用户登出 |
| GET | `/auth/me` | 获取当前用户信息 |

### 3.2 用户管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/users` | 获取用户列表（管理员） |
| GET | `/api/users/<id>` | 获取用户详情 |
| PUT | `/api/users/<id>` | 更新用户信息 |
| DELETE | `/api/users/<id>` | 删除用户（管理员） |

### 3.3 项目管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects` | 获取我的项目列表 |
| POST | `/api/projects` | 创建项目 |
| GET | `/api/projects/<id>` | 获取项目详情 |
| PUT | `/api/projects/<id>` | 更新项目 |
| DELETE | `/api/projects/<id>` | 删除项目 |
| POST | `/api/projects/<id>/members` | 添加项目成员 |
| DELETE | `/api/projects/<id>/members/<user_id>` | 移除项目成员 |

### 3.4 任务管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects/<id>/tasks` | 获取项目任务列表 |
| POST | `/api/projects/<id>/tasks` | 创建任务 |
| GET | `/api/tasks/<id>` | 获取任务详情 |
| PUT | `/api/tasks/<id>` | 更新任务 |
| DELETE | `/api/tasks/<id>` | 删除任务 |
| POST | `/api/tasks/<id>/claim` | 认领任务 |
| POST | `/api/tasks/<id>/complete` | 完成任务 |

### 3.5 文档管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects/<id>/documents` | 获取项目文档列表 |
| POST | `/api/documents` | 创建文档 |
| GET | `/api/documents/<id>` | 获取文档详情 |
| PUT | `/api/documents/<id>` | 更新文档 |
| DELETE | `/api/documents/<id>` | 删除文档 |
| GET | `/api/documents/<id>/download` | 下载文档 |

### 3.6 文件管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/projects/<id>/files` | 获取项目文件列表 |
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/<id>/download` | 下载文件 |
| DELETE | `/api/files/<id>` | 删除文件 |

### 3.7 WebSocket 实时协作

| Event | 方向 | 描述 |
|-------|------|------|
| `join_doc` | Client → Server | 加入文档 Room |
| `leave_doc` | Client → Server | 离开文档 Room |
| `sync_update` | Bidirectional | Yjs CRDT 同步更新 |
| `awareness_update` | Bidirectional | Cursor/选区同步 |

---

## 4. 目录结构

```
coworking/
├── docs/
│   ├── requirements.md      # 需求说明
│   └── architecture.md      # 系统架构
├── backend/
│   ├── app/
│   │   ├── __init__.py     # Flask app factory
│   │   ├── config.py        # 配置
│   │   ├── models/         # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── document.py
│   │   │   └── file.py
│   │   ├── routes/         # 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── projects.py
│   │   │   ├── tasks.py
│   │   │   ├── documents.py
│   │   │   └── files.py
│   │   ├── services/       # 业务逻辑
│   │   │   └── collab.py   # 协作服务
│   │   └── utils/          # 工具函数
│   │       └── decorators.py
│   ├── uploads/            # 文件上传目录
│   ├── requirements.txt
│   └── run.py              # 启动脚本
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   │   ├── app.js      # 主应用逻辑
│   │   │   ├── editor.js   # Cell 编辑器
│   │   │   ├── yjs-setup.js # Yjs CRDT 配置
│   │   │   └── socket.js   # WebSocket 客户端
│   │   └── index.html      # 入口页面
│   └── login.html
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 5. 防爬虫策略

| 策略 | 实现 |
|------|------|
| 登录认证 | 所有 API 需登录后访问 |
| 请求频率限制 | Flask-Limiter：每分钟 60 请求/IP |
| CORS 控制 | 仅允许已知域名 |
| User-Agent 检测 | 拒绝异常爬虫 UA |
| 敏感操作验证码 | 关键操作需二次验证 |

---

## 6. 待细化

- [ ] Yjs 后端 WebSocket Provider 具体实现
- [ ] Cell 编辑器前端组件详细设计
- [ ] Docker 部署细节
- [ ] 权限控制细化（项目级别 vs 系统级别）

---

*架构基于 Flask + Flask-SocketIO + MySQL + Yjs 技术栈设计*
