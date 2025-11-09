# Configuration System Guide

AI Auto-Annotation Tool 配置系统完整指南

## 📖 概述

配置系统支持：
- ✅ **YAML 格式** - 人类可读的配置文件
- ✅ **多环境支持** - Development, Production, Test
- ✅ **环境变量支持** - 使用 `${VAR}` 语法
- ✅ **配置验证** - Pydantic 自动验证
- ✅ **配置合并** - 基础配置 + 环境覆盖
- ✅ **CLI 工具** - 命令行管理配置

## 🗂️ 配置文件结构

### 完整配置示例

```yaml
# 环境类型: development, production, test
environment: development
debug: true

# 数据库配置
database:
  host: localhost
  port: 5432
  user: postgres
  password: your_password
  database: qwen3vl_db
  pool_size: 20
  max_overflow: 10

# Redis 配置
redis:
  host: localhost
  port: 6379
  db: 0
  password: null
  max_connections: 50

# API 服务器配置
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: true
  cors_origins:
    - http://localhost:3000
  request_timeout: 300

# 文件存储配置
storage:
  root: ./storage
  images_dir: images
  datasets_dir: datasets
  models_dir: models
  max_file_size_mb: 100

# AI 模型配置
models:
  qwen3vl_api_url: http://localhost:9292/v1
  qwen3vl_model: qwen3-vl-30b
  qwen3vl_timeout: 60

  hunyuan_api_url: http://localhost:8000
  hunyuan_api_key: your_key
  hunyuan_timeout: 120

# 训练配置
training:
  default_epochs: 100
  default_batch_size: 16
  default_img_size: 640
  default_device: cuda:0
  checkpoint_interval: 10
  early_stopping_patience: 50

# Celery 配置
celery:
  broker_url: null  # 默认使用 Redis
  result_backend: null
  task_time_limit: 3600
  task_soft_time_limit: 3000
  worker_prefetch_multiplier: 4
  worker_max_tasks_per_child: 1000

# 日志配置
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  log_file: null
  rotation: "1 day"
  retention: "30 days"
```

### 配置项说明

#### Environment (环境)
- `environment`: 环境类型 (`development`, `production`, `test`)
- `debug`: 调试模式 (boolean)

#### Database (数据库)
- `host`: 数据库主机地址
- `port`: 端口号 (默认 5432)
- `user`: 数据库用户名
- `password`: 数据库密码
- `database`: 数据库名称
- `pool_size`: 连接池大小
- `max_overflow`: 最大溢出连接数

#### Redis (缓存)
- `host`: Redis 主机地址
- `port`: 端口号 (默认 6379)
- `db`: 数据库编号 (0-15)
- `password`: Redis 密码 (可选)
- `max_connections`: 最大连接数

#### API (API 服务器)
- `host`: 监听地址
- `port`: 监听端口
- `workers`: Worker 进程数
- `reload`: 自动重载 (开发环境使用)
- `cors_origins`: 允许的 CORS 源
- `request_timeout`: 请求超时时间(秒)

#### Storage (文件存储)
- `root`: 存储根目录
- `images_dir`: 图片子目录
- `datasets_dir`: 数据集子目录
- `models_dir`: 模型子目录
- `max_file_size_mb`: 最大文件大小(MB)

#### Models (AI 模型)
- `qwen3vl_api_url`: Qwen3-VL API 地址
- `qwen3vl_model`: 模型名称
- `qwen3vl_timeout`: 请求超时(秒)
- `hunyuan_api_url`: Hunyuan Image API 地址
- `hunyuan_api_key`: API 密钥
- `hunyuan_timeout`: 请求超时(秒)

#### Training (训练)
- `default_epochs`: 默认训练轮数
- `default_batch_size`: 默认批次大小
- `default_img_size`: 默认图片尺寸
- `default_device`: 默认设备 (cuda:0/cpu)
- `checkpoint_interval`: 检查点保存间隔
- `early_stopping_patience`: 早停容忍轮数

#### Celery (任务队列)
- `broker_url`: 消息代理 URL (默认使用 Redis)
- `result_backend`: 结果后端 URL (默认使用 Redis)
- `task_time_limit`: 任务硬超时(秒)
- `task_soft_time_limit`: 任务软超时(秒)
- `worker_prefetch_multiplier`: Worker 预取倍数
- `worker_max_tasks_per_child`: Worker 子进程最大任务数

#### Logging (日志)
- `level`: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- `format`: 日志格式
- `log_file`: 日志文件路径 (null 表示仅控制台输出)
- `rotation`: 日志轮转策略
- `retention`: 日志保留时间

## 🔧 CLI 命令

### 初始化配置文件

创建新的配置文件：

```bash
# 使用默认配置
qwen3vl-annotate config init

# 指定环境
qwen3vl-annotate config init --env production

# 指定输出路径
qwen3vl-annotate config init --output my-config.yaml

# 强制覆盖现有文件
qwen3vl-annotate config init --force
```

### 验证配置文件

检查配置文件的有效性：

```bash
qwen3vl-annotate config validate config.yaml
```

输出示例：
```
✓ Configuration file is valid: config.yaml

Environment: development
Debug: True

Database: localhost:5432/qwen3vl_dev
Redis: localhost:6379/0
API: 0.0.0.0:8000
Storage: ./storage_dev

Warnings:
⚠ Database password is empty
⚠ Hunyuan API key is not set
```

### 查看配置

显示完整配置或特定部分：

```bash
# 显示完整配置
qwen3vl-annotate config show config.yaml

# 只显示数据库配置
qwen3vl-annotate config show config.yaml --section database

# 只显示模型配置
qwen3vl-annotate config show config.yaml --section models
```

### 获取配置值

获取特定配置项的值：

```bash
# 获取数据库主机
qwen3vl-annotate config get config.yaml database.host

# 获取 API 端口
qwen3vl-annotate config get config.yaml api.port

# 获取训练批次大小
qwen3vl-annotate config get config.yaml training.default_batch_size
```

### 设置配置值

修改配置项：

```bash
# 设置数据库主机
qwen3vl-annotate config set config.yaml database.host "192.168.1.100"

# 设置 API 端口
qwen3vl-annotate config set config.yaml api.port 9000

# 设置调试模式
qwen3vl-annotate config set config.yaml debug false
```

### 合并配置文件

合并两个配置文件：

```bash
# 合并到基础配置
qwen3vl-annotate config merge base.yaml override.yaml

# 输出到新文件
qwen3vl-annotate config merge base.yaml override.yaml --output merged.yaml
```

### 列出配置模板

查看可用的配置模板：

```bash
qwen3vl-annotate config list-templates
```

输出：
```
Available configuration templates:
  - development: configs/config.development.yaml
  - production: configs/config.production.yaml
  - test: configs/config.test.yaml
  - example: configs/config.example.yaml
```

## 🌍 多环境配置

### 开发环境 (Development)

```yaml
environment: development
debug: true

database:
  database: qwen3vl_dev
  pool_size: 10

api:
  reload: true
  workers: 2

training:
  default_epochs: 50
  default_batch_size: 8

logging:
  level: DEBUG
  log_file: logs/dev.log
```

### 生产环境 (Production)

```yaml
environment: production
debug: false

database:
  host: ${DB_HOST}
  database: qwen3vl_prod
  pool_size: 50

api:
  reload: false
  workers: 8
  cors_origins:
    - https://yourdomain.com

training:
  default_epochs: 200
  default_batch_size: 32

logging:
  level: INFO
  log_file: /var/log/qwen3vl/app.log
```

### 测试环境 (Test)

```yaml
environment: test
debug: true

database:
  database: qwen3vl_test
  pool_size: 5

redis:
  db: 1  # 使用不同的 DB

api:
  port: 8001
  workers: 1

training:
  default_device: cpu
  default_epochs: 10

logging:
  level: DEBUG
```

## 🔐 环境变量支持

配置文件中可以使用环境变量：

```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT:5432}  # 默认值 5432
  password: ${DB_PASSWORD}

models:
  qwen3vl_api_url: ${QWEN3VL_API_URL}
  hunyuan_api_key: ${HUNYUAN_API_KEY}
```

设置环境变量：

```bash
export DB_HOST=192.168.1.100
export DB_PASSWORD=secret123
export QWEN3VL_API_URL=http://qwen3vl-api:9292/v1
export HUNYUAN_API_KEY=your-api-key-here
```

## 🐍 Python API 使用

### 加载配置

```python
from backend.core.config_loader import ConfigLoader, get_config

# 自动从默认路径加载
config = ConfigLoader.load()

# 从指定文件加载
config = ConfigLoader.load('my-config.yaml')

# 从特定路径加载
config = ConfigLoader.load_from_file('/path/to/config.yaml')

# 使用全局配置实例
config = get_config()
```

### 访问配置

```python
# 数据库 URL
db_url = config.database.get_url()
# postgresql://user:pass@localhost:5432/db

# Redis URL
redis_url = config.redis.get_url()
# redis://localhost:6379/0

# API 配置
api_host = config.api.host
api_port = config.api.port

# 模型配置
qwen_url = config.models.qwen3vl_api_url
```

### 保存配置

```python
from backend.core.config_loader import ConfigLoader, Config

config = Config()
config.database.host = "192.168.1.100"
config.api.port = 9000

ConfigLoader.save(config, 'new-config.yaml')
```

### 合并配置

```python
base_config = ConfigLoader.load('base.yaml')
override = {'database': {'host': '192.168.1.100'}}

merged = ConfigLoader.merge_configs(base_config, override)
```

## 📍 配置文件搜索路径

系统按以下顺序搜索配置文件：

1. `config.yaml` (当前目录)
2. `config.yml` (当前目录)
3. `.qwen3vl.yaml` (当前目录)
4. `.qwen3vl.yml` (当前目录)
5. `~/.qwen3vl/config.yaml` (用户目录)
6. 如果都找不到，使用默认配置

指定配置文件：

```bash
# 使用环境变量
export QWEN3VL_CONFIG=/path/to/config.yaml

# 使用 CLI 参数
qwen3vl-annotate --config /path/to/config.yaml ...
```

## ✅ 最佳实践

### 1. 使用环境专用配置

```bash
# 开发环境
qwen3vl-annotate config init --env development

# 生产环境
qwen3vl-annotate config init --env production
```

### 2. 敏感信息使用环境变量

```yaml
# ✓ 推荐
database:
  password: ${DB_PASSWORD}

# ✗ 不推荐
database:
  password: "hardcoded_password"
```

### 3. 验证配置

部署前始终验证配置：

```bash
qwen3vl-annotate config validate config.yaml
```

### 4. 版本控制

```bash
# 提交示例配置
git add config.example.yaml
git add config.development.yaml

# 不要提交包含敏感信息的配置
echo "config.production.yaml" >> .gitignore
echo "config.yaml" >> .gitignore
```

### 5. 配置继承

使用基础配置 + 环境覆盖：

```bash
# 基础配置
cp config.example.yaml config.base.yaml

# 环境配置 (只包含差异)
cat > config.prod.yaml <<EOF
environment: production
debug: false
database:
  host: prod-db.example.com
EOF

# 合并
qwen3vl-annotate config merge config.base.yaml config.prod.yaml -o config.yaml
```

## 🆘 故障排查

### 配置文件找不到

```bash
# 检查搜索路径
ls -la config.yaml config.yml .qwen3vl.yaml
ls -la ~/.qwen3vl/config.yaml

# 使用绝对路径
qwen3vl-annotate --config /absolute/path/to/config.yaml
```

### 验证失败

```bash
# 查看详细错误信息
qwen3vl-annotate config validate config.yaml

# 检查 YAML 语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### 环境变量未替换

确保在启动前设置环境变量：

```bash
# 设置变量
export DB_HOST=localhost
export DB_PASSWORD=secret

# 验证
echo $DB_HOST
echo $DB_PASSWORD

# 启动应用
uvicorn backend.api.main:app
```

## 📚 参考

- Pydantic: https://docs.pydantic.dev/
- YAML: https://yaml.org/
- FastAPI Settings: https://fastapi.tiangolo.com/advanced/settings/
