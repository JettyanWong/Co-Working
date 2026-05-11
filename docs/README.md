# Co-working — 团队协作平台

## 项目简介

Co-working 是一个轻量级团队协作平台，支持项目管理、任务跟踪、实时协作文档编辑和文件共享。前端使用原生 HTML/JS，后端基于 Flask，通过 Yjs CRDT 实现文档实时协同编辑。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + Vanilla JS + CodeMirror 5 + marked.js + Yjs |
| 实时协作 | Yjs CRDT + Socket.IO (Flask-SocketIO) |
| 后端 | Python 3.9+ / Flask 3.0 |
| 数据库 | SQLite (开发) / MySQL 8.0 (生产) |
| 部署 | Docker + docker-compose + Nginx |

## 核心功能

### 用户系统
- 注册 / 登录（bcrypt 密码加密，session 认证）
- 管理员审核机制：新用户注册后状态为"待审核"，需管理员通过后方可登录
- 角色管理：管理员 / 普通成员，管理员可启用/禁用账号

### 项目管理
- 创建项目、添加成员
- 四级权限控制：Owner > Admin > Member > Viewer
- 项目内任务、文档、文件统一管理

### 任务跟踪
- 创建任务、指定负责人
- 任务状态：待处理 → 进行中 → 已完成
- 认领任务、完成任务
- 仅任务创建者或项目 Owner 可删除，仅负责人或项目 Owner 可改变状态

### 协作文档
- Cell 结构编辑器（文本/代码/图片三种 cell 类型）
- Markdown 实时渲染（marked.js）
- 代码高亮编辑（CodeMirror）
- WYSIWYG 表格编辑器（支持 Excel 粘贴、添加/删除行列）
- 图片 cell（上传后即时显示）
- Yjs CRDT 多人实时协同编辑
- 导出为 .md 文件

### 文件管理
- 文件上传（支持关联项目）
- 在线预览：图片、Markdown 渲染、代码文本、PDF
- 下载 / 删除

### 管理后台
- 用户审核（通过/拒绝）
- 用户管理（角色变更、启用/禁用、删除）
- 仅管理员可访问

## 快速开始

### 环境要求
- Python 3.9+
- pip
- (可选) Docker + docker-compose

### 本地开发

```bash
# 克隆项目
git clone <repo-url>
cd Co-working/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py
```

服务默认运行在 `http://localhost:5001`。

### 首次设置管理员

```bash
# 先注册一个普通用户（通过 Web 页面）
# 然后运行：
cd backend
python make_admin.py <你的用户名>
```

### Docker 部署

```bash
docker-compose up -d
```

这会启动：
- MySQL 8.0 数据库（端口 3306）
- Flask 应用 + Nginx 反向代理（端口 80）

## 项目结构

```
Co-working/
├── docker-compose.yml
├── Dockerfile
├── docs/
│   ├── README.md          # 本文档
│   ├── requirements.md    # 需求文档
│   └── architecture.md    # 架构文档
├── backend/
│   ├── run.py             # 应用入口
│   ├── make_admin.py      # 管理员提权脚本
│   ├── requirements.txt   # Python 依赖
│   ├── .env               # 环境变量
│   └── app/
│       ├── __init__.py    # Flask 工厂函数
│       ├── config.py      # 配置类
│       ├── models/        # 数据模型 (6张表)
│       │   ├── user.py        # 用户
│       │   ├── project.py     # 项目 + 成员
│       │   ├── task.py        # 任务
│       │   ├── document.py    # 文档 + Cell
│       │   └── file.py        # 文件
│       ├── routes/        # API 路由 (6个蓝图)
│       │   ├── auth.py        # /auth/*
│       │   ├── users.py       # /api/users/*
│       │   ├── projects.py    # /api/projects/*
│       │   ├── tasks.py       # /api/tasks/*
│       │   ├── documents.py   # /api/documents/*
│       │   └── files.py       # /api/files/*
│       ├── services/      # 业务服务
│       │   └── collab.py      # Yjs 实时协作 (Socket.IO)
│       └── utils/
│           └── decorators.py  # 项目权限装饰器
└── frontend/
    ├── login.html         # 登录/注册页
    └── static/
        ├── index.html     # 主导航页
        ├── project.html   # 项目详情页
        ├── editor.html    # 协作文档编辑器
        ├── file-view.html # 文件预览页
        ├── admin.html     # 管理后台
        └── js/
            ├── app.js         # 主应用逻辑
            └── yjs-setup.js   # Yjs 客户端
```

## 数据库模型

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `users` | 用户 | id, username, email, password, role, status, created_at |
| `projects` | 项目 | id, name, description, owner_id, created_at |
| `project_members` | 项目成员 | id, project_id, user_id, role |
| `tasks` | 任务 | id, project_id, title, description, status, assignee_id, created_by |
| `documents` | 文档 | id, project_id, title, owner_id, created_at |
| `document_cells` | 文档 Cell | id, document_id, type, content, cell_order |
| `files` | 文件 | id, project_id, filename, filepath, size, uploader_id |

## API 概览

### 认证 (`/auth`)
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/auth/register` | 注册 | 公开 |
| POST | `/auth/login` | 登录 | 公开 |
| POST | `/auth/logout` | 退出 | 登录 |
| GET | `/auth/me` | 当前用户信息 | 登录 |

### 用户管理 (`/api/users`)
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/users` | 用户列表 | 管理员 |
| GET | `/api/users/<id>` | 用户详情 | 登录 |
| PUT | `/api/users/<id>` | 更新用户 | 本人/管理员 |
| DELETE | `/api/users/<id>` | 删除用户 | 管理员 |
| POST | `/api/users/<id>/approve` | 审核通过 | 管理员 |
| POST | `/api/users/<id>/reject` | 审核拒绝 | 管理员 |

### 项目 (`/api/projects`)
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/projects` | 我的项目列表 | 登录 |
| POST | `/api/projects` | 创建项目 | 登录 |
| GET | `/api/projects/<id>` | 项目详情 | 项目成员 |
| PUT | `/api/projects/<id>` | 更新项目 | Owner/Admin |
| DELETE | `/api/projects/<id>` | 删除项目 | Owner |

### 任务
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/projects/<id>/tasks` | 项目任务列表 | 项目成员 |
| POST | `/api/projects/<id>/tasks` | 创建任务 | 项目成员 |
| POST | `/api/tasks/<id>/claim` | 认领任务 | 项目成员 |
| POST | `/api/tasks/<id>/complete` | 完成任务 | 负责人/Owner |
| DELETE | `/api/tasks/<id>` | 删除任务 | 创建者/Owner |

### 文档
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/documents` | 我的文档列表 | 登录 |
| POST | `/api/documents` | 创建文档 | 登录 |
| GET | `/api/documents/<id>` | 文档详情（含 cells） | 项目成员 |
| PUT | `/api/documents/<id>` | 更新文档 | 文档 Owner |
| DELETE | `/api/documents/<id>` | 删除文档 | 文档 Owner |
| GET | `/api/documents/<id>/download` | 导出为 .md | 项目成员 |

### 文件
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/files` | 上传文件 (multipart) | 登录 |
| GET | `/api/files/<id>/view` | 在线查看 | 项目成员 |
| GET | `/api/files/<id>/download` | 下载文件 | 项目成员 |
| DELETE | `/api/files/<id>` | 删除文件 | 上传者 |

### 实时协作 (WebSocket)
| 事件 | 方向 | 说明 |
|------|------|------|
| `join_doc` | C→S | 加入文档协同 |
| `leave_doc` | C→S | 离开文档协同 |
| `yjs_sync` | ↔ | Yjs CRDT 更新同步 |
| `cell_add` | C→S | 新增 cell |
| `cell_delete` | C→S | 删除 cell |
| `cursor_update` | C→S | 光标位置广播 |

## 配置说明

`.env` 文件：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FLASK_ENV` | 运行环境 | `development` |
| `SECRET_KEY` | Flask session 密钥 | 随机字符串 |
| `DATABASE_URL` | 数据库连接 | 空=SQLite, 非空=MySQL |
| `UPLOAD_FOLDER` | 文件上传目录 | `./uploads` |

数据库选择逻辑：
- `DATABASE_URL` 有值 → 使用指定数据库
- `FLASK_ENV=development` 且无 `DATABASE_URL` → SQLite (`instance/coworking.db`)
- `FLASK_ENV=production` 且无 `DATABASE_URL` → MySQL (`root:password@localhost:3306/coworking`)

## 权限体系

### 用户角色
| 角色 | 说明 |
|------|------|
| `admin` | 系统管理员，可管理所有用户 |
| `member` | 普通成员，使用项目功能 |

### 用户状态
| 状态 | 说明 |
|------|------|
| `pending` | 待审核，不可登录 |
| `active` | 正常，可登录使用 |
| `disabled` | 已禁用，不可登录 |

### 项目角色
| 角色 | 权限 |
|------|------|
| `owner` | 完全控制（删除项目、管理成员、删除任何任务等） |
| `admin` | 管理成员、创建/管理任务 |
| `member` | 创建任务、认领任务、上传文件、编辑文档 |
| `viewer` | 只读访问 |

## 文档编辑器特性

- **三种 Cell 类型**：文本（Markdown 渲染）、代码（CodeMirror 编辑）、图片（上传+显示）
- **WYSIWYG 表格**：可视化编辑表格内容、添加/删除行列、Excel 粘贴转表格
- **实时协作**：基于 Yjs CRDT，多人同时编辑自动合并冲突
- **所见即所得**：文本 cell 编辑时实时渲染 Markdown 预览
