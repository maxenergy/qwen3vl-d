# 自动标注工具系统 - 详细开发计划

## 项目概览

**项目名称:** Auto Annotation Tool System
**目标:** 基于Hunyuan Image 3.0 + Qwen3-VL的自动数据集生成与标注系统
**开发周期:** 8-12周 (MVP: 4-6周)
**技术栈:** FastAPI + Gradio + PostgreSQL + Redis + Celery + Ultralytics YOLO

---

## Phase 1: 项目基础架构搭建 (Week 1)

### 1.1 创建项目目录结构 (0.5天)

**任务清单:**
- [ ] 创建完整的目录结构
- [ ] 初始化Git仓库
- [ ] 配置.gitignore

**交付物:**
```
auto-annotation-tool/
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── workers/
│   ├── core/
│   └── utils/
├── frontend/
│   ├── web/
│   └── cli/
├── data/
├── models/
├── configs/
├── scripts/
├── tests/
└── docs/
```

### 1.2 配置开发环境 (1天)

**任务清单:**
- [ ] 创建requirements.txt
- [ ] 创建pyproject.toml
- [ ] 配置.env.example
- [ ] 创建docker-compose.yml (开发环境)
- [ ] 编写setup.py

**依赖包:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.9
redis>=5.0.0
celery>=5.3.0
pydantic>=2.4.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
pillow>=10.1.0
gradio>=4.7.0
typer>=0.9.0
rich>=13.7.0
loguru>=0.7.2
ultralytics>=8.0.0
openai>=1.3.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

### 1.3 数据库初始化脚本 (1天)

**任务清单:**
- [ ] 编写create_tables.sql
- [ ] 编写setup_database.py
- [ ] 创建初始迁移
- [ ] 编写种子数据脚本

**SQL文件:**
- `scripts/sql/01_create_tables.sql` - 创建所有表
- `scripts/sql/02_create_indexes.sql` - 创建索引
- `scripts/sql/03_seed_data.sql` - 初始数据

### 1.4 核心配置模块 (1.5天)

**任务清单:**
- [ ] `backend/core/config.py` - 配置管理
- [ ] `backend/core/database.py` - 数据库连接
- [ ] `backend/core/logging.py` - 日志配置
- [ ] `backend/core/security.py` - 安全配置

**关键功能:**
- Pydantic Settings加载环境变量
- SQLAlchemy引擎和会话管理
- 结构化日志输出
- 异常处理中间件

---

## Phase 2: 数据模型与API基础 (Week 2)

### 2.1 SQLAlchemy数据模型 (2天)

**任务清单:**
- [ ] `backend/models/project.py` - 项目和标签模型
- [ ] `backend/models/dataset.py` - 数据集版本模型
- [ ] `backend/models/generation.py` - 图片生成相关模型
- [ ] `backend/models/annotation.py` - 标注相关模型
- [ ] `backend/models/training.py` - 训练相关模型
- [ ] `backend/models/__init__.py` - 模型导入

**模型列表:**
- Project
- Label
- DatasetVersion
- GenerationTask
- Image
- AnnotationTask
- Annotation
- TrainingTask
- Model
- TaskLog

### 2.2 Pydantic Schema定义 (1.5天)

**任务清单:**
- [ ] `backend/schemas/project.py`
- [ ] `backend/schemas/generation.py`
- [ ] `backend/schemas/annotation.py`
- [ ] `backend/schemas/dataset.py`
- [ ] `backend/schemas/training.py`
- [ ] `backend/schemas/common.py` - 通用Schema

**Schema类型:**
- Request Schema (xxxCreate, xxxUpdate)
- Response Schema (xxxResponse, xxxDetail)
- 分页Schema (PagedResponse)

### 2.3 FastAPI主应用和路由框架 (1.5天)

**任务清单:**
- [ ] `backend/api/main.py` - 主应用
- [ ] `backend/api/dependencies.py` - 依赖注入
- [ ] `backend/api/routes/__init__.py`
- [ ] 配置CORS
- [ ] 配置异常处理
- [ ] 配置中间件

**路由模块骨架:**
- `/api/v1/projects`
- `/api/v1/generation`
- `/api/v1/annotation`
- `/api/v1/datasets`
- `/api/v1/training`
- `/api/v1/models`

### 2.4 数据库迁移工具 (1天)

**任务清单:**
- [ ] 配置Alembic
- [ ] 创建初始迁移
- [ ] 编写迁移脚本模板
- [ ] 测试升级/降级

---

## Phase 3: 项目管理模块 (Week 3, Day 1-2)

### 3.1 项目CRUD API (1天)

**API端点:**
- `POST /api/v1/projects` - 创建项目
- `GET /api/v1/projects` - 列出项目
- `GET /api/v1/projects/{id}` - 项目详情
- `PATCH /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目

**文件:**
- `backend/api/routes/projects.py`
- `backend/services/project_service.py`

### 3.2 标签管理API (0.5天)

**API端点:**
- `POST /api/v1/projects/{id}/labels` - 添加标签
- `GET /api/v1/projects/{id}/labels` - 列出标签
- `PATCH /api/v1/labels/{id}` - 更新标签
- `DELETE /api/v1/labels/{id}` - 删除标签

### 3.3 项目统计API (0.5天)

**API端点:**
- `GET /api/v1/projects/{id}/stats` - 项目统计
- `GET /api/v1/stats` - 全局统计

---

## Phase 4: 图片生成模块 (Week 3, Day 3-5 + Week 4, Day 1-2)

### 4.1 Hunyuan集成服务 (1.5天)

**任务清单:**
- [ ] `backend/services/image_generator.py`
- [ ] Hunyuan API客户端封装
- [ ] 图片存储逻辑
- [ ] 错误处理和重试

**功能:**
- 文本生成图片
- 图片+文本生成
- 批量生成
- 分辨率配置

### 4.2 提示词模板系统 (1天)

**任务清单:**
- [ ] `configs/templates/` - 模板配置文件
- [ ] `backend/services/prompt_template.py` - 模板引擎
- [ ] 变量替换逻辑
- [ ] 模板验证

**模板示例:**
```yaml
# traffic_smoking.yaml
name: "交通场景-吸烟检测"
description: "生成街道吸烟场景图片"
template: "A {time} photo of {location} with people smoking cigarettes, {weather}, realistic"
variables:
  time: [daytime, night, dusk, dawn]
  location: [street, park, bus stop, train station]
  weather: [sunny, cloudy, rainy]
```

### 4.3 图片生成API (1天)

**API端点:**
- `POST /api/v1/projects/{id}/generation/tasks` - 创建生成任务
- `GET /api/v1/generation/tasks/{id}` - 任务状态
- `GET /api/v1/generation/tasks/{id}/images` - 生成的图片
- `POST /api/v1/generation/tasks/{id}/pause` - 暂停任务
- `POST /api/v1/generation/tasks/{id}/resume` - 恢复任务
- `POST /api/v1/generation/tasks/{id}/cancel` - 取消任务

**文件:**
- `backend/api/routes/generation.py`

### 4.4 图片审核API (0.5天)

**API端点:**
- `POST /api/v1/images/{id}/review` - 审核单张图片
- `POST /api/v1/images/batch-review` - 批量审核
- `GET /api/v1/images/{id}` - 图片详情
- `GET /api/v1/images/{id}/thumbnail` - 缩略图
- `GET /api/v1/images/{id}/full` - 完整图片

### 4.5 Celery异步任务 (2天)

**任务清单:**
- [ ] `backend/workers/celery_app.py` - Celery配置
- [ ] `backend/workers/generation_tasks.py` - 生成任务
- [ ] 任务状态更新
- [ ] 断点续传逻辑
- [ ] 错误处理和重试

**Celery任务:**
- `generate_images_task` - 主生成任务
- `generate_single_image_task` - 单张生成
- `cleanup_failed_images_task` - 清理失败图片

---

## Phase 5: 自动标注模块 (Week 4, Day 3-5 + Week 5, Day 1-2)

### 5.1 Qwen3-VL集成服务 (1.5天)

**任务清单:**
- [ ] `backend/services/auto_annotator.py`
- [ ] 现有Qwen3-VL客户端集成
- [ ] 坐标转换 (0-1000 → YOLO格式)
- [ ] 置信度过滤
- [ ] 批量推理优化

**功能:**
- 调用现有qwen3vl_d包
- 支持多类别检测
- 结果可视化
- 错误处理

### 5.2 自动标注API (1天)

**API端点:**
- `POST /api/v1/projects/{id}/annotation/tasks` - 创建标注任务
- `GET /api/v1/annotation/tasks/{id}` - 任务状态
- `GET /api/v1/annotation/tasks/{id}/results` - 标注结果
- `POST /api/v1/annotation/tasks/{id}/pause` - 暂停
- `POST /api/v1/annotation/tasks/{id}/resume` - 恢复

**文件:**
- `backend/api/routes/annotation.py`
- `backend/workers/annotation_tasks.py`

### 5.3 标注审核API (1天)

**API端点:**
- `GET /api/v1/annotations/{id}` - 标注详情
- `POST /api/v1/annotations/{id}/verify` - 校验标注
- `PATCH /api/v1/annotations/{id}` - 修正标注
- `DELETE /api/v1/annotations/{id}` - 删除标注
- `GET /api/v1/images/{id}/annotated` - 标注可视化

### 5.4 批量操作API (0.5天)

**API端点:**
- `DELETE /api/v1/annotation/tasks/{id}/labels/{label}` - 删除某类别所有标注
- `POST /api/v1/annotation/tasks/{id}/re-annotate` - 重新标注
- `POST /api/v1/annotations/batch-verify` - 批量校验

---

## Phase 6: 数据集管理模块 (Week 5, Day 3-5 + Week 6, Day 1)

### 6.1 YOLO格式转换器 (1.5天)

**任务清单:**
- [ ] `backend/services/converters/yolo_converter.py`
- [ ] 坐标转换 (归一化)
- [ ] data.yaml生成
- [ ] train/val/test划分
- [ ] 文件复制/软链接

**功能:**
- 转换annotations到YOLO格式
- 生成data.yaml配置
- 数据集划分 (8:1:1)
- 类别映射

### 6.2 COCO格式转换器 (1天)

**任务清单:**
- [ ] `backend/services/converters/coco_converter.py`
- [ ] COCO JSON生成
- [ ] 图片信息整理
- [ ] categories配置

### 6.3 数据集版本API (1天)

**API端点:**
- `POST /api/v1/projects/{id}/datasets` - 创建数据集版本
- `GET /api/v1/projects/{id}/datasets` - 版本列表
- `GET /api/v1/datasets/{id}` - 版本详情
- `GET /api/v1/datasets/{id}/download/{format}` - 下载数据集

**文件:**
- `backend/api/routes/datasets.py`
- `backend/services/dataset_service.py`

### 6.4 K-Fold数据集生成 (0.5天)

**任务清单:**
- [ ] `backend/services/kfold_generator.py`
- [ ] sklearn StratifiedKFold集成
- [ ] 生成多个fold配置

### 6.5 数据增强配置 (1天)

**任务清单:**
- [ ] `backend/services/augmentation.py`
- [ ] 增强参数配置
- [ ] YOLO增强集成

---

## Phase 7: 训练模块 (Week 6, Day 2-5 + Week 7, Day 1)

### 7.1 YOLO训练服务封装 (1.5天)

**任务清单:**
- [ ] `backend/services/yolo_trainer.py`
- [ ] Ultralytics YOLO集成
- [ ] 训练配置生成
- [ ] 预训练模型下载
- [ ] GPU资源管理

### 7.2 训练任务API (1天)

**API端点:**
- `POST /api/v1/projects/{id}/training/tasks` - 创建训练任务
- `GET /api/v1/training/tasks/{id}` - 任务状态
- `GET /api/v1/training/tasks/{id}/logs` - 训练日志
- `POST /api/v1/training/tasks/{id}/stop` - 停止训练

**文件:**
- `backend/api/routes/training.py`
- `backend/workers/training_tasks.py`

### 7.3 训练监控API (1天)

**API端点:**
- `GET /api/v1/training/tasks/{id}/metrics` - 实时指标
- `GET /api/v1/training/tasks/{id}/results` - 训练结果
- `GET /api/v1/training/tasks/{id}/charts/{chart}` - 图表

### 7.4 TensorBoard集成 (0.5天)

**任务清单:**
- [ ] TensorBoard进程管理
- [ ] API端点返回URL
- [ ] 自动启动/停止

---

## Phase 8: 模型管理模块 (Week 7, Day 2-3)

### 8.1 模型存储与版本管理 (0.5天)

**任务清单:**
- [ ] `backend/services/model_service.py`
- [ ] 模型文件管理
- [ ] 版本标记
- [ ] 最佳模型选择

### 8.2 模型推理API (1天)

**API端点:**
- `GET /api/v1/projects/{id}/models` - 模型列表
- `GET /api/v1/models/{id}` - 模型详情
- `POST /api/v1/models/{id}/predict` - 单张预测
- `POST /api/v1/models/{id}/mark-best` - 标记最佳

**文件:**
- `backend/api/routes/models.py`

### 8.3 模型评估API (0.5天)

**API端点:**
- `POST /api/v1/models/{id}/evaluate` - 测试集评估
- `GET /api/v1/models/{id}/metrics` - 性能指标

---

## Phase 9: Web界面开发 (Week 7, Day 4-5 + Week 8)

### 9.1 Gradio主应用框架 (0.5天)

**任务清单:**
- [ ] `frontend/web/app.py` - 主应用
- [ ] Tab结构搭建
- [ ] API客户端配置
- [ ] 样式配置

### 9.2 项目管理页面 (1天)

**任务清单:**
- [ ] `frontend/web/pages/project_page.py`
- [ ] 项目选择器
- [ ] 标签管理组件
- [ ] 统计展示

### 9.3 图片生成页面 (1.5天)

**任务清单:**
- [ ] `frontend/web/pages/generation_page.py`
- [ ] 提示词输入
- [ ] 模板选择器
- [ ] 批量上传
- [ ] 任务进度展示
- [ ] 图片预览和审核

### 9.4 标注审核页面 (1.5天)

**任务清单:**
- [ ] `frontend/web/pages/annotation_page.py`
- [ ] 标注任务配置
- [ ] 图片展示
- [ ] 标注框可视化
- [ ] 校验界面
- [ ] 批量操作

### 9.5 数据集管理页面 (1天)

**任务清单:**
- [ ] `frontend/web/pages/dataset_page.py`
- [ ] 版本创建表单
- [ ] 版本列表
- [ ] 统计可视化
- [ ] 下载链接

### 9.6 训练监控页面 (1.5天)

**任务清单:**
- [ ] `frontend/web/pages/training_page.py`
- [ ] 训练配置表单
- [ ] 进度监控
- [ ] 指标曲线
- [ ] 日志查看

### 9.7 模型测试页面 (1天)

**任务清单:**
- [ ] `frontend/web/pages/model_page.py`
- [ ] 模型列表
- [ ] 单张测试
- [ ] 结果展示
- [ ] 性能对比

---

## Phase 10: CLI工具开发 (Week 9, Day 1-2)

**任务清单:**
- [ ] `frontend/cli/main.py` - Typer主应用
- [ ] `frontend/cli/commands/project.py`
- [ ] `frontend/cli/commands/generate.py`
- [ ] `frontend/cli/commands/annotate.py`
- [ ] `frontend/cli/commands/train.py`

**命令示例:**
```bash
# 项目管理
auto-annotate project create "smoking_detection"
auto-annotate project list

# 生成图片
auto-annotate generate --project smoking_detection --num 100 --template traffic

# 标注
auto-annotate annotate --project smoking_detection --task gen_task_001

# 训练
auto-annotate train --dataset v1.0 --yolo v8 --size n
```

---

## Phase 11: 测试与文档 (Week 9, Day 3-5)

### 11.1 单元测试 (1.5天)

**任务清单:**
- [ ] `tests/unit/test_models.py`
- [ ] `tests/unit/test_services.py`
- [ ] `tests/unit/test_converters.py`
- [ ] pytest配置

### 11.2 集成测试 (1天)

**任务清单:**
- [ ] `tests/integration/test_api.py`
- [ ] `tests/integration/test_workflows.py`

### 11.3 文档编写 (0.5天)

**任务清单:**
- [ ] `docs/API_REFERENCE.md` - API文档
- [ ] `docs/USER_GUIDE.md` - 用户指南
- [ ] `docs/DEPLOYMENT.md` - 部署文档
- [ ] `README.md` - 项目说明

---

## Phase 12: 部署配置 (Week 10)

### 12.1 Docker配置 (1天)

**任务清单:**
- [ ] `Dockerfile`
- [ ] `docker-compose.yml` (生产环境)
- [ ] `.dockerignore`
- [ ] 多阶段构建优化

### 12.2 部署脚本 (0.5天)

**任务清单:**
- [ ] `scripts/deploy.sh`
- [ ] `scripts/backup.sh`
- [ ] `scripts/restore.sh`

### 12.3 监控与日志 (0.5天)

**任务清单:**
- [ ] 日志轮转配置
- [ ] 健康检查端点
- [ ] 性能监控

---

## 里程碑 (Milestones)

### M1: 基础架构完成 (Week 2结束)
- ✅ 项目结构搭建
- ✅ 数据库初始化
- ✅ API框架就绪
- ✅ 数据模型完成

### M2: 核心功能完成 (Week 6结束)
- ✅ 图片生成模块
- ✅ 自动标注模块
- ✅ 数据集转换模块
- ✅ 训练模块

### M3: MVP发布 (Week 8结束)
- ✅ Web界面完成
- ✅ 基础功能可用
- ✅ 文档完成

### M4: V1.0发布 (Week 10结束)
- ✅ CLI工具
- ✅ 完整测试
- ✅ 生产部署

---

## 风险管理

### 高风险项
1. **Hunyuan模型部署** - 显存需求大
   - 缓解: 提供API调用方案
2. **并发任务资源竞争** - GPU争抢
   - 缓解: 任务队列优先级管理
3. **大量图片存储** - 磁盘空间
   - 缓解: 图片压缩和归档

### 中风险项
1. **Qwen3-VL API稳定性**
   - 缓解: 重试机制和错误处理
2. **训练时间过长**
   - 缓解: 提供快速训练预设

---

## 资源需求

### 开发环境
- Python 3.10+
- PostgreSQL 15
- Redis 7
- NVIDIA GPU (RTX 4090 24GB)
- 至少500GB磁盘空间

### 第三方服务
- Hunyuan Image 3.0 (本地或API)
- Qwen3-VL API (现有)

---

## 下一步行动

1. ✅ 确认开发计划
2. ⏭️ 创建API接口文档
3. ⏭️ 开始Phase 1实施
