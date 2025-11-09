# API测试指南

## Phase 2.3 已完成的功能

### 已实现的API端点

**基础端点:**
- `GET /` - API根路径
- `GET /api/v1/health` - 健康检查
- `GET /api/docs` - Swagger文档（开发模式）
- `GET /api/redoc` - ReDoc文档（开发模式）

**项目管理 (Projects):**
- `POST /api/v1/projects` - 创建项目
- `GET /api/v1/projects` - 获取项目列表（分页）
- `GET /api/v1/projects/{project_id}` - 获取项目详情
- `PATCH /api/v1/projects/{project_id}` - 更新项目
- `DELETE /api/v1/projects/{project_id}` - 删除项目

**标签管理 (Labels):**
- `POST /api/v1/projects/{project_id}/labels` - 添加标签
- `GET /api/v1/projects/{project_id}/labels` - 获取标签列表
- `PATCH /api/v1/labels/{label_id}` - 更新标签
- `DELETE /api/v1/labels/{label_id}` - 删除标签

## 前置准备

### 1. 启动数据库

```bash
# 使用Docker Compose启动PostgreSQL和Redis
docker-compose up -d

# 等待数据库就绪
sleep 5
```

### 2. 初始化数据库

```bash
# 运行数据库初始化脚本
python scripts/setup_database.py
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，确保数据库配置正确
# DATABASE_URL=postgresql://user:password@localhost:5432/auto_annotation
```

## 启动API服务器

### 方法1: 直接运行

```bash
# 确保已安装依赖
# pip install -r requirements.txt

# 启动FastAPI服务器
python -m backend.api.main

# 或使用uvicorn
uvicorn backend.api.main:app --reload --port 8000
```

### 方法2: 开发模式

```bash
# 带自动重载
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

访问：
- API文档: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- 健康检查: http://localhost:8000/api/v1/health

## API测试示例

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

期望响应:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T10:00:00Z",
  "services": {
    "database": "ok",
    "redis": "not_implemented",
    "celery": "not_implemented",
    "hunyuan": "not_implemented",
    "qwen3vl": "not_implemented"
  },
  "version": "1.0.0"
}
```

### 2. 创建项目

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "smoking_detection",
    "description": "检测吸烟行为和烟头",
    "labels": [
      {
        "name": "smoking_person",
        "color": "#FF0000",
        "description": "正在吸烟的人"
      },
      {
        "name": "cigarette",
        "color": "#FFA500",
        "description": "烟头或香烟"
      }
    ]
  }'
```

期望响应:
```json
{
  "id": 1,
  "name": "smoking_detection",
  "description": "检测吸烟行为和烟头",
  "status": "active",
  "created_at": "2025-11-09T10:00:00Z",
  "updated_at": "2025-11-09T10:00:00Z",
  "labels": [
    {
      "id": 1,
      "project_id": 1,
      "name": "smoking_person",
      "color": "#FF0000",
      "description": "正在吸烟的人",
      "is_active": true,
      "created_at": "2025-11-09T10:00:00Z"
    },
    {
      "id": 2,
      "project_id": 1,
      "name": "cigarette",
      "color": "#FFA500",
      "description": "烟头或香烟",
      "is_active": true,
      "created_at": "2025-11-09T10:00:00Z"
    }
  ]
}
```

### 3. 获取项目列表

```bash
curl http://localhost:8000/api/v1/projects?page=1&per_page=20
```

### 4. 获取项目详情

```bash
curl http://localhost:8000/api/v1/projects/1
```

### 5. 更新项目

```bash
curl -X PATCH http://localhost:8000/api/v1/projects/1 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述"
  }'
```

### 6. 添加标签

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/labels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cigarette_butt",
    "color": "#808080",
    "description": "地上的烟头"
  }'
```

### 7. 获取标签列表

```bash
curl http://localhost:8000/api/v1/projects/1/labels
```

## 使用Swagger UI测试

1. 访问 http://localhost:8000/api/docs
2. 点击任意API端点
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"
6. 查看响应

## 验证要点

### ✅ Phase 2.3 完成标准

- [x] FastAPI应用正常启动
- [x] 健康检查端点返回正确
- [x] Swagger文档可访问
- [x] 数据库连接成功
- [x] CORS中间件配置正确
- [x] 异常处理正常工作
- [x] 项目CRUD操作正常
- [x] 标签CRUD操作正常
- [x] 分页功能正常
- [x] 数据验证（Pydantic）正常
- [x] 响应格式符合设计

### 🧪 测试检查清单

**基础功能:**
- [ ] 根路径返回正确信息
- [ ] 健康检查返回数据库状态
- [ ] Swagger文档正常显示

**项目管理:**
- [ ] 创建项目成功
- [ ] 项目名称唯一性验证
- [ ] 获取项目列表（分页）
- [ ] 获取项目详情
- [ ] 更新项目
- [ ] 删除项目（软删除）

**标签管理:**
- [ ] 添加标签成功
- [ ] 标签名称唯一性验证（同项目内）
- [ ] 获取标签列表
- [ ] 更新标签
- [ ] 删除标签

**错误处理:**
- [ ] 404错误（项目不存在）
- [ ] 409错误（名称冲突）
- [ ] 422错误（数据验证失败）
- [ ] 500错误（内部错误）

## 下一步

Phase 3 将实现：
- 图片生成API
- 标注API
- 数据集API
- 训练API
- 模型API
