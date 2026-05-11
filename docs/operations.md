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
