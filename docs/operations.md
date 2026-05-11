# 运维操作指南

## 云端服务（阿里云 ECS）

### 启动服务

```bash
ssh root@47.107.36.182
cd /opt/coworking
docker-compose up -d
```

### 停止服务

```bash
ssh root@47.107.36.182
cd /opt/coworking
docker-compose down
```

### 重启服务

```bash
ssh root@47.107.36.182 "cd /opt/coworking && docker-compose down && docker-compose up -d"
```

### 查看日志

```bash
ssh root@47.107.36.182 "cd /opt/coworking && docker-compose logs -f app"
```

### 查看状态

```bash
ssh root@47.107.36.182 "cd /opt/coworking && docker-compose ps"
```

### 重新构建（代码更新后）

```bash
scp /Volumes/Jett/projects/Co-working/backend/app/config.py root@47.107.36.182:/opt/coworking/backend/app/
ssh root@47.107.36.182 "cd /opt/coworking && docker-compose up -d --build"
```

> 只改了后端文件需重建；只改前端文件则上传后重启容器即可（`docker-compose restart app`，无需 `--build`）。

### 设立管理员

```bash
ssh root@47.107.36.182 "cd /opt/coworking && docker-compose exec db mysql -u root -p coworking -e \"UPDATE users SET role='admin', status='active' WHERE username='<用户名>';\""
```

---

## 本地开发

### 启动服务

```bash
cd /Volumes/Jett/projects/Co-working/backend
source venv/bin/activate
python run.py
```

服务运行在 `http://localhost:5001`

### 停止服务

按 `Ctrl+C`

### 设立管理员

```bash
cd /Volumes/Jett/projects/Co-working/backend
python make_admin.py <用户名>
```

---

## 文件上传

本地文件上传到云端（代码修改后，完整部署）：

```bash
# 打包（排除虚拟环境和上传文件）
cd /Volumes/Jett/projects/Co-working
tar --exclude='backend/venv' --exclude='backend/uploads' --exclude='backend/instance' \
    --exclude='__pycache__' --exclude='.DS_Store' --exclude='*.tar.gz' \
    -czf /tmp/coworking.tar.gz .

# 上传到服务器
scp /tmp/coworking.tar.gz root@47.107.36.182:/opt/coworking/

# 解压并重建
ssh root@47.107.36.182 "cd /opt/coworking && tar -xzf coworking.tar.gz && rm coworking.tar.gz && docker-compose down && docker-compose up -d --build"
```

> 数据库数据（用户、项目等）存储在 Docker volume 中，重新构建不会丢失。

---

## Git 版本管理

仓库地址：`https://github.com/JettyanWong/Co-Working.git`

### 提交并推送修改

```bash
cd /Volumes/Jett/projects/Co-working

# 查看修改了哪些文件
git status

# 添加所有修改的文件
git add .

# 提交（commit message 描述本次修改）
git commit -m "类型: 修改说明"

# 推送到 GitHub
git push origin main
```

Commit message 类型约定：`feat`（新功能）、`fix`（修复）、`refactor`（重构）、`docs`（文档）、`style`（样式）、`test`（测试）、`chore`（杂项）。

### 拉取远程更新（先于本地修改之前）

```bash
cd /Volumes/Jett/projects/Co-working
git pull origin main
```

### 解决推送冲突

如果推送时遇到 `rejected` 错误，说明远程有新提交：

```bash
# 拉取并 rebase（推荐，保持历史线性）
git pull origin main --rebase

# 解决冲突后继续
git add .
git rebase --continue

# 推送
git push origin main
```

如果不想 rebase，也可以用 merge：

```bash
git pull origin main --no-rebase
# 解决冲突后
git add .
git commit -m "merge: 合并远程更新"
git push origin main
```

### 本地未跟踪的文件不提交

`.gitignore` 已排除：`venv/`、`__pycache__/`、`*.pyc`、`.env`、`uploads/`、`instance/`、`*.db`、`.DS_Store`。新增敏感文件或大文件请先加入 `.gitignore`。

### 回退某次提交（未推送）

```bash
# 回退最近一次 commit，保留文件修改
git reset --soft HEAD~1
```

### 查看提交历史

```bash
git log --oneline -10
```
