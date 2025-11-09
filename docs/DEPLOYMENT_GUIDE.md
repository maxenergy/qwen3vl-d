# Deployment Guide

AI Auto-Annotation Tool Docker 部署完整指南

## 📖 概述

本系统采用 Docker 容器化部署，支持：
- ✅ **Docker Compose** - 一键部署所有服务
- ✅ **多环境支持** - Development / Production
- ✅ **自动扩展** - 支持多副本部署
- ✅ **健康检查** - 自动监控和重启
- ✅ **持久化存储** - 数据卷管理
- ✅ **Nginx 反向代理** - 负载均衡和 SSL

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                    │
│                    Port 80/443 (HTTP/HTTPS)                  │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │    Frontend     │              │    Backend     │
    │  (React + Vite) │              │   (FastAPI)    │
    │   Port 80       │              │   Port 8000    │
    └─────────────────┘              └────────┬───────┘
                                              │
            ┌─────────────────────────────────┼────────────────┐
            │                                 │                │
    ┌───────▼────────┐    ┌──────────▼──────────┐    ┌───────▼────────┐
    │   PostgreSQL   │    │   Redis (Cache)     │    │ Celery Workers │
    │   Port 5432    │    │   Port 6379         │    │  (4 workers)   │
    └────────────────┘    └─────────────────────┘    └────────────────┘
```

## 📦 Docker 镜像

### 后端镜像 (Multi-stage)
- **base**: Python 3.11 + 系统依赖
- **development**: 开发环境（热重载）
- **production**: 生产环境（优化）
- **celery-worker**: Celery 工作进程

### 前端镜像 (Multi-stage)
- **build**: Node 20 构建阶段
- **development**: Vite 开发服务器
- **production**: Nginx + 静态文件

## 🚀 快速开始

### 前置要求

```bash
# 检查 Docker 版本
docker --version  # >= 20.10
docker-compose --version  # >= 1.29

# 检查系统资源
free -h  # 至少 8GB RAM
df -h    # 至少 50GB 磁盘空间
```

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/qwen3vl-d.git
cd qwen3vl-d
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑配置
nano .env
```

必须配置的变量：
```bash
# 数据库
DB_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# AI 模型
QWEN3VL_API_URL=http://your-qwen-api:9292/v1
HUNYUAN_API_URL=http://your-hunyuan-api:8000
HUNYUAN_API_KEY=your_api_key
```

### 3. 启动服务

```bash
# 开发环境
./scripts/deploy.sh development up

# 生产环境
./scripts/deploy.sh production up
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 访问服务
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🛠️ 部署脚本使用

### 基本命令

```bash
./scripts/deploy.sh [environment] [action]
```

### 环境选项

- `development` / `dev` - 开发环境
- `production` / `prod` - 生产环境

### 操作选项

#### 启动服务
```bash
./scripts/deploy.sh production up
```

#### 停止服务
```bash
./scripts/deploy.sh production down
```

#### 重启服务
```bash
./scripts/deploy.sh production restart
```

#### 构建镜像
```bash
./scripts/deploy.sh production build
```

#### 重建并启动
```bash
./scripts/deploy.sh production rebuild
```

#### 查看日志
```bash
./scripts/deploy.sh production logs
```

#### 查看状态
```bash
./scripts/deploy.sh production status
```

#### 运行数据库迁移
```bash
./scripts/deploy.sh production migrate
```

#### 进入容器
```bash
# 进入 backend 容器
./scripts/deploy.sh production shell backend

# 进入 postgres 容器
./scripts/deploy.sh production shell postgres
```

#### 清理
```bash
./scripts/deploy.sh production clean
```

## 🔧 手动 Docker Compose 命令

### 基础操作

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启单个服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend

# 查看服务状态
docker-compose ps
```

### 构建

```bash
# 构建所有镜像
docker-compose build

# 构建单个服务
docker-compose build backend

# 无缓存构建
docker-compose build --no-cache
```

### 扩展

```bash
# 扩展 backend 到 3 个实例
docker-compose up -d --scale backend=3

# 扩展 celery-worker 到 5 个实例
docker-compose up -d --scale celery-worker=5
```

### 执行命令

```bash
# 在 backend 容器中执行命令
docker-compose exec backend python manage.py

# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 创建超级用户
docker-compose exec backend python scripts/create_superuser.py

# 进入 PostgreSQL
docker-compose exec postgres psql -U postgres -d qwen3vl_db
```

## 🌍 生产环境部署

### 1. 准备服务器

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 2. 创建生产目录

```bash
sudo mkdir -p /var/lib/qwen3vl/{postgres,redis,storage}
sudo mkdir -p /var/log/qwen3vl/nginx
sudo chown -R $USER:$USER /var/lib/qwen3vl
sudo chown -R $USER:$USER /var/log/qwen3vl
```

### 3. 配置 SSL 证书

```bash
# 使用 Let's Encrypt
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到 nginx 目录
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### 4. 配置环境变量

```bash
# 生产环境配置
cat > .env <<EOF
# 环境
ENVIRONMENT=production
DEBUG=false

# 数据库
DB_USER=postgres
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=qwen3vl_prod

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# AI 模型
QWEN3VL_API_URL=http://your-qwen-api:9292/v1
HUNYUAN_API_URL=http://your-hunyuan-api:8000
HUNYUAN_API_KEY=your_api_key

# 前端
VITE_API_BASE_URL=https://your-domain.com

EOF
```

### 5. 启动生产环境

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 检查服务
docker-compose ps

# 运行迁移
docker-compose exec backend alembic upgrade head
```

### 6. 配置自动启动

```bash
# 创建 systemd service
sudo nano /etc/systemd/system/qwen3vl.service
```

```ini
[Unit]
Description=Qwen3VL Auto-Annotation Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/qwen3vl-d
ExecStart=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
User=your-user

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable qwen3vl
sudo systemctl start qwen3vl
```

## 📊 监控和维护

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df

# 查看网络
docker network ls
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f backend

# 查看最近 100 行
docker-compose logs --tail=100 backend

# 保存日志到文件
docker-compose logs > logs/docker-$(date +%Y%m%d).log
```

### 备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres qwen3vl_db > backup-$(date +%Y%m%d).sql

# 备份 Redis
docker-compose exec redis redis-cli SAVE
docker cp qwen3vl-redis:/data/dump.rdb backup-redis-$(date +%Y%m%d).rdb

# 备份存储目录
tar -czf storage-backup-$(date +%Y%m%d).tar.gz storage/
```

### 恢复

```bash
# 恢复数据库
docker-compose exec -T postgres psql -U postgres qwen3vl_db < backup-20231201.sql

# 恢复 Redis
docker cp backup-redis-20231201.rdb qwen3vl-redis:/data/dump.rdb
docker-compose restart redis

# 恢复存储
tar -xzf storage-backup-20231201.tar.gz
```

## 🔍 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs

# 检查容器状态
docker-compose ps

# 检查网络
docker network inspect qwen3vl-network

# 重建容器
docker-compose down
docker-compose up -d --force-recreate
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 日志
docker-compose logs postgres

# 检查连接
docker-compose exec postgres pg_isready -U postgres

# 进入数据库
docker-compose exec postgres psql -U postgres
```

### Redis 连接失败

```bash
# 检查 Redis 日志
docker-compose logs redis

# 测试连接
docker-compose exec redis redis-cli ping

# 检查密码
docker-compose exec redis redis-cli -a your_password ping
```

### 内存不足

```bash
# 查看内存使用
docker stats

# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有未使用资源
docker system prune -a
```

## 🔐 安全建议

### 1. 使用强密码

```bash
# 生成安全密码
openssl rand -base64 32
```

### 2. 配置防火墙

```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 定期更新

```bash
# 更新 Docker 镜像
docker-compose pull
docker-compose up -d
```

### 4. 限制资源

在 `docker-compose.prod.yml` 中配置：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 5. 使用 secrets

```bash
# 使用 Docker secrets（Swarm mode）
echo "your_password" | docker secret create db_password -
```

## 📋 检查清单

### 部署前

- [ ] 配置所有环境变量
- [ ] 创建必要的目录
- [ ] 配置 SSL 证书（生产环境）
- [ ] 检查防火墙规则
- [ ] 备份现有数据

### 部署后

- [ ] 验证所有服务正常运行
- [ ] 检查健康检查状态
- [ ] 测试 API 端点
- [ ] 测试前端访问
- [ ] 运行数据库迁移
- [ ] 配置监控和告警
- [ ] 设置自动备份

## 📚 参考资源

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

如有问题，请查看项目 Issues 或联系维护团队。
