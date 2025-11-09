# API 接口文档

AI Auto-Annotation Tool 完整 API 参考文档

## 基础信息

**Base URL:** `http://localhost:8000/api/v1`
**认证方式:** 暂不需要 (MVP版本)
**内容类型:** `application/json`
**字符编码:** `UTF-8`

**API 版本:** v1.0
**总端点数:** 52 个

## 端点概览

| 模块 | 端点数 | 描述 |
|------|--------|------|
| [1. 项目管理](#1-项目管理-api) | 9 | 项目和标签的 CRUD 操作 |
| [2. 图片生成](#2-图片生成-api) | 8 | Hunyuan 图片生成任务管理 |
| [3. 图片审核](#3-图片审核-api) | 7 | 图片审核和批量操作 |
| [4. 自动标注](#4-自动标注-api) | 12 | Qwen3-VL 自动标注和审核 |
| [5. 数据集管理](#5-数据集管理-api) | 8 | YOLO/COCO 数据集生成和导出 |
| [6. 训练管理](#6-训练管理-api) | 8 | YOLO 模型训练和管理 |

---

## 1. 项目管理 API

### 1.1 创建项目

**端点:** `POST /api/v1/projects`

**请求体:**
```json
{
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
}
```

**响应:** `201 Created`
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
      "name": "smoking_person",
      "color": "#FF0000",
      "description": "正在吸烟的人",
      "is_active": true
    },
    {
      "id": 2,
      "name": "cigarette",
      "color": "#FFA500",
      "description": "烟头或香烟",
      "is_active": true
    }
  ]
}
```

### 1.2 获取项目列表

**端点:** `GET /api/v1/projects`

**查询参数:**
- `page` (int, 默认: 1) - 页码
- `per_page` (int, 默认: 20) - 每页数量
- `status` (string, 可选) - 过滤状态: active, archived

**响应:** `200 OK`
```json
{
  "total": 10,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "items": [
    {
      "id": 1,
      "name": "smoking_detection",
      "description": "检测吸烟行为和烟头",
      "status": "active",
      "created_at": "2025-11-09T10:00:00Z",
      "label_count": 2,
      "image_count": 150,
      "annotation_count": 680
    }
  ]
}
```

### 1.3 获取项目详情

**端点:** `GET /api/v1/projects/{project_id}`

**响应:** `200 OK`
```json
{
  "id": 1,
  "name": "smoking_detection",
  "description": "检测吸烟行为和烟头",
  "status": "active",
  "created_at": "2025-11-09T10:00:00Z",
  "updated_at": "2025-11-09T10:00:00Z",
  "labels": [...],
  "versions": [
    {
      "id": 1,
      "version": "v1.0",
      "total_images": 100,
      "status": "ready"
    }
  ],
  "statistics": {
    "total_images": 150,
    "approved_images": 120,
    "total_annotations": 680,
    "models_trained": 3
  }
}
```

### 1.4 更新项目

**端点:** `PATCH /api/v1/projects/{project_id}`

**请求体:**
```json
{
  "description": "更新后的描述",
  "status": "active"
}
```

**响应:** `200 OK` (返回更新后的项目)

### 1.5 删除项目

**端点:** `DELETE /api/v1/projects/{project_id}`

**响应:** `204 No Content`

---

## 2. 标签管理 API

### 2.1 添加标签

**端点:** `POST /api/v1/projects/{project_id}/labels`

**请求体:**
```json
{
  "name": "cigarette_butt",
  "color": "#808080",
  "description": "地上的烟头"
}
```

**响应:** `201 Created`

### 2.2 更新标签

**端点:** `PATCH /api/v1/labels/{label_id}`

**请求体:**
```json
{
  "color": "#A0A0A0",
  "is_active": false
}
```

**响应:** `200 OK`

### 2.3 删除标签

**端点:** `DELETE /api/v1/labels/{label_id}`

**响应:** `204 No Content`

---

## 2. 图片生成 API

### 2.1 创建生成任务

**端点:** `POST /api/v1/projects/{project_id}/generation/tasks`

**请求体 (文本模式):**
```json
{
  "task_name": "batch_001_smoking_scenes",
  "num_images": 100,
  "resolution": "640x640",
  "mode": "text_to_image",
  "prompts": [
    "A person smoking a cigarette on the street during daytime",
    "Cigarette butt on the ground near a trash can",
    "People smoking at a bus stop at night"
  ]
}
```

**请求体 (使用模板):**
```json
{
  "task_name": "batch_002_template",
  "num_images": 50,
  "resolution": "1024x1024",
  "mode": "text_to_image",
  "prompt_template": "traffic_smoking",
  "template_params": {
    "time": ["daytime", "night"],
    "location": ["street", "park"]
  }
}
```

**请求体 (图片+文本模式):**
```json
{
  "task_name": "batch_003_reference",
  "num_images": 30,
  "resolution": "640x640",
  "mode": "image_to_image",
  "reference_images": [
    "/path/to/ref1.jpg",
    "/path/to/ref2.jpg"
  ],
  "reference_prompts": [
    "Generate similar scene with smoking person",
    "Same style but different location"
  ]
}
```

**响应:** `201 Created`
```json
{
  "task_id": 123,
  "status": "pending",
  "num_images": 100,
  "estimated_time": 600,
  "created_at": "2025-11-09T10:00:00Z"
}
```

### 2.2 获取项目的生成任务列表

**端点:** `GET /api/v1/projects/{project_id}/generation/tasks`

**查询参数:**
- `page` (int, 默认: 1) - 页码
- `per_page` (int, 默认: 20) - 每页数量
- `status` (string, 可选) - 过滤状态

**响应:** `200 OK`

### 2.3 获取生成任务详情

**端点:** `GET /api/v1/projects/{project_id}/generation/tasks/{task_id}`

**响应:** `200 OK`
```json
{
  "task_id": 123,
  "task_name": "batch_001_smoking_scenes",
  "status": "running",
  "progress": 45,
  "generated_count": 45,
  "total": 100,
  "reviewed_count": 0,
  "approved_count": 0,
  "elapsed_time": 270,
  "estimated_remaining": 330,
  "created_at": "2025-11-09T10:00:00Z",
  "started_at": "2025-11-09T10:01:00Z"
}
```

**状态值:**
- `pending` - 等待执行
- `running` - 正在生成
- `paused` - 已暂停
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

### 2.4 删除生成任务

**端点:** `DELETE /api/v1/projects/{project_id}/generation/tasks/{task_id}`

**响应:** `204 No Content`

### 2.5 获取任务的生成图片列表

**端点:** `GET /api/v1/projects/{project_id}/generation/tasks/{task_id}/images`

**查询参数:**
- `page` (int) - 页码
- `per_page` (int) - 每页数量
- `review_status` (string) - pending, approved, rejected

**响应:** `200 OK`
```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "images": [
    {
      "id": 1001,
      "filename": "gen_001.jpg",
      "resolution": "640x640",
      "file_size": 1048576,
      "prompt": "A person smoking...",
      "review_status": "pending",
      "created_at": "2025-11-09T10:05:00Z",
      "thumbnail_url": "/api/v1/images/1001/thumbnail",
      "full_url": "/api/v1/images/1001/full"
    }
  ]
}
```

### 2.6 批量创建生成任务

**端点:** `POST /api/v1/projects/{project_id}/generation/batch`

**请求体:**
```json
{
  "tasks": [
    {
      "name": "batch_001",
      "prompt": "A person smoking",
      "batch_size": 50
    },
    {
      "name": "batch_002",
      "prompt": "Cigarette on ground",
      "batch_size": 50
    }
  ]
}
```

**响应:** `201 Created`

### 2.7 获取提示词模板列表

**端点:** `GET /api/v1/templates`

**响应:** `200 OK`
```json
{
  "templates": [
    {
      "name": "general_scene",
      "category": "general",
      "description": "通用场景模板",
      "variables": ["time", "location", "weather"]
    }
  ]
}
```

### 2.8 获取单个模板详情

**端点:** `GET /api/v1/templates/{template_name}`

**响应:** `200 OK`

---

## 3. 图片审核 API

### 3.1 获取项目图片列表

**端点:** `GET /api/v1/projects/{project_id}/images`

**查询参数:**
- `page` (int) - 页码
- `per_page` (int) - 每页数量
- `review_status` (string) - pending, approved, rejected

**响应:** `200 OK`

### 3.2 获取图片详情

**端点:** `GET /api/v1/projects/{project_id}/images/{image_id}`

**响应:** `200 OK`

### 3.3 审核图片

**端点:** `PATCH /api/v1/projects/{project_id}/images/{image_id}/review`

**请求体:**
```json
{
  "status": "approved",
  "notes": "Good quality image"
}
```

**响应:** `200 OK`

### 3.4 批量审核图片

**端点:** `POST /api/v1/projects/{project_id}/images/review/batch`

**请求体:**
```json
{
  "image_ids": [1001, 1002, 1003],
  "status": "approved"
}
```

**响应:** `200 OK`
```json
{
  "updated_count": 3
}
```

### 3.5 删除图片

**端点:** `DELETE /api/v1/projects/{project_id}/images/{image_id}`

**响应:** `204 No Content`

### 3.6 批量删除图片

**端点:** `POST /api/v1/projects/{project_id}/images/delete/batch`

**请求体:**
```json
{
  "image_ids": [1, 2, 3, 4, 5]
}
```

**响应:** `204 No Content`

### 3.7 获取图片统计信息

**端点:** `GET /api/v1/projects/{project_id}/images/statistics`

**响应:** `200 OK`
```json
{
  "total": 100,
  "pending": 20,
  "approved": 70,
  "rejected": 10,
  "avg_file_size_mb": 1.2
}
```

---

## 4. 自动标注 API

标注任务使用 Qwen3-VL 进行自动目标检测和边界框生成。

### 4.1 创建标注任务

**端点:** `POST /api/v1/projects/{project_id}/annotation/tasks`

**请求体:**
```json
{
  "task_name": "annotate_batch_001",
  "dataset_version": "v1.0",
  "label_names": ["smoking_person", "cigarette"],
  "image_ids": [1001, 1002, 1003],
  "confidence_threshold": 0.3,
  "max_detections_per_image": 100,
  "api_endpoint": "http://192.168.8.147:9292/v1",
  "model_name": "qwen3-vl-30b"
}
```

**或使用所有已批准图片:**
```json
{
  "task_name": "annotate_all_approved",
  "label_names": ["smoking_person", "cigarette"],
  "image_source": "all_approved",
  "generation_task_id": 123,
  "confidence_threshold": 0.3
}
```

**响应:** `201 Created`
```json
{
  "task_id": 456,
  "status": "pending",
  "total_images": 100,
  "estimated_time": 300
}
```

### 4.2 获取项目的标注任务列表

**端点:** `GET /api/v1/projects/{project_id}/annotation/tasks`

**查询参数:**
- `page` (int) - 页码
- `per_page` (int) - 每页数量
- `status` (string, 可选) - 过滤状态

**响应:** `200 OK`

### 4.3 获取标注任务详情

**端点:** `GET /api/v1/projects/{project_id}/annotation/tasks/{task_id}`

**响应:** `200 OK`
```json
{
  "task_id": 456,
  "task_name": "annotate_batch_001",
  "status": "running",
  "progress": 60,
  "total_images": 100,
  "annotated_images": 60,
  "total_annotations": 180,
  "avg_detections_per_image": 3.0,
  "avg_time_per_image": 2.5,
  "elapsed_time": 150,
  "estimated_remaining": 100
}
```

### 4.4 删除标注任务

**端点:** `DELETE /api/v1/projects/{project_id}/annotation/tasks/{task_id}`

**响应:** `204 No Content`

### 4.5 获取任务的所有标注

**端点:** `GET /api/v1/projects/{project_id}/annotation/tasks/{task_id}/annotations`

**查询参数:**
- `page` (int)
- `per_page` (int)
- `image_id` (int, 可选) - 查询特定图片

**响应:** `200 OK`
```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "results": [
    {
      "image_id": 1001,
      "filename": "gen_001.jpg",
      "image_url": "/api/v1/images/1001/full",
      "visualization_url": "/api/v1/images/1001/annotated",
      "annotations": [
        {
          "id": 5001,
          "label": "smoking_person",
          "label_id": 1,
          "bbox": [100, 200, 300, 400],
          "confidence": 0.85,
          "normalized_coords": {
            "x": 0.5,
            "y": 0.6,
            "w": 0.2,
            "h": 0.25
          },
          "is_verified": false
        }
      ],
      "annotation_count": 3
    }
  ]
}
```

### 4.6 获取图片的所有标注

**端点:** `GET /api/v1/projects/{project_id}/images/{image_id}/annotations`

**响应:** `200 OK`
```json
{
  "image_id": 1001,
  "annotations": [
    {
      "id": 5001,
      "label_id": 1,
      "label_name": "smoking_person",
      "bbox": [100, 200, 300, 400],
      "confidence": 0.85,
      "is_verified": true
    }
  ]
}
```

### 4.7 获取单个标注详情

**端点:** `GET /api/v1/projects/{project_id}/annotations/{annotation_id}`

**响应:** `200 OK`

### 4.8 审核/修改标注

**端点:** `PATCH /api/v1/projects/{project_id}/annotations/{annotation_id}/review`

**请求体:**
```json
{
  "is_correct": true,
  "correction_bbox": [105, 205, 305, 405],
  "notes": "Slightly adjusted bbox"
}
```

**响应:** `200 OK`

### 4.9 删除单个标注

**端点:** `DELETE /api/v1/projects/{project_id}/annotations/{annotation_id}`

**响应:** `204 No Content`

### 4.10 批量删除标注

**端点:** `POST /api/v1/projects/{project_id}/annotations/batch-delete`

**请求体:**
```json
{
  "annotation_ids": [5001, 5002, 5003]
}
```

**响应:** `204 No Content`

### 4.11 按标签批量操作

**端点:** `POST /api/v1/projects/{project_id}/annotations/batch-by-label`

**请求体:**
```json
{
  "label_id": 2,
  "action": "delete",
  "task_id": 456
}
```

**响应:** `204 No Content`

### 4.12 获取标注统计信息

**端点:** `GET /api/v1/projects/{project_id}/annotations/statistics`

**响应:** `200 OK`
```json
{
  "total_annotations": 680,
  "by_label": {
    "smoking_person": 400,
    "cigarette": 280
  },
  "verified_count": 650,
  "avg_confidence": 0.87
}
```

---

## 5. 数据集管理 API

支持 YOLO 和 COCO 格式的数据集生成、版本管理和导出功能。

### 5.1 创建数据集版本

**端点:** `POST /api/v1/projects/{project_id}/datasets`

**请求体:**
```json
{
  "version": "v1.0",
  "description": "Initial dataset with 100 images",
  "source_task_ids": {
    "generation": [123, 124],
    "annotation": [456]
  },
  "split_ratio": {
    "train": 0.8,
    "val": 0.1,
    "test": 0.1
  },
  "random_seed": 42,
  "export_formats": ["yolo", "coco"],
  "augmentation": {
    "enabled": true,
    "horizontal_flip": true,
    "vertical_flip": false,
    "rotation": 10,
    "brightness": 0.2,
    "contrast": 0.2,
    "mosaic": 1.0,
    "mixup": 0.5
  },
  "kfold": {
    "enabled": true,
    "n_splits": 5,
    "shuffle": true
  }
}
```

**响应:** `201 Created`
```json
{
  "version_id": 789,
  "version": "v1.0",
  "status": "building",
  "estimated_time": 30
}
```

### 5.2 获取数据集版本列表

**端点:** `GET /api/v1/projects/{project_id}/datasets`

**响应:** `200 OK`
```json
{
  "versions": [
    {
      "id": 789,
      "version": "v1.0",
      "description": "Initial dataset",
      "status": "ready",
      "total_images": 100,
      "total_annotations": 350,
      "train_count": 80,
      "val_count": 10,
      "test_count": 10,
      "export_formats": ["yolo", "coco"],
      "created_at": "2025-11-09T12:00:00Z"
    }
  ]
}
```

### 5.3 获取数据集详情

**端点:** `GET /api/v1/projects/{project_id}/datasets/{dataset_id}`

**响应:** `200 OK`
```json
{
  "id": 789,
  "version": "v1.0",
  "description": "Initial dataset",
  "status": "ready",
  "created_at": "2025-11-09T12:00:00Z",
  "statistics": {
    "total_images": 100,
    "total_annotations": 350,
    "label_distribution": {
      "smoking_person": 200,
      "cigarette": 150
    },
    "split_distribution": {
      "train": {
        "images": 80,
        "annotations": 280
      },
      "val": {
        "images": 10,
        "annotations": 35
      },
      "test": {
        "images": 10,
        "annotations": 35
      }
    }
  },
  "config": {
    "split_ratio": {...},
    "augmentation": {...},
    "kfold": {...}
  },
  "download_urls": {
    "yolo": "/api/v1/datasets/789/download/yolo",
    "coco": "/api/v1/datasets/789/download/coco"
  }
}
```

### 5.4 删除数据集

**端点:** `DELETE /api/v1/projects/{project_id}/datasets/{dataset_id}`

**响应:** `204 No Content`

### 5.5 导出数据集

**端点:** `POST /api/v1/projects/{project_id}/datasets/{dataset_id}/export`

**请求体:**
```json
{
  "format": "yolo",
  "include_augmented": false
}
```

**响应:** `200 OK`
```json
{
  "download_url": "/api/v1/datasets/789/download/yolo.zip",
  "file_size_mb": 145.3
}
```

### 5.6 重新生成数据集

**端点:** `POST /api/v1/projects/{project_id}/datasets/{dataset_id}/regenerate`

**请求体:**
```json
{
  "regenerate_splits": true,
  "regenerate_augmentation": true
}
```

**响应:** `200 OK`

### 5.7 获取数据集统计

**端点:** `GET /api/v1/projects/{project_id}/datasets/{dataset_id}/statistics`

**响应:** `200 OK`
```json
{
  "total_images": 100,
  "total_annotations": 350,
  "split_distribution": {
    "train": 80,
    "val": 10,
    "test": 10
  },
  "label_distribution": {
    "smoking_person": 200,
    "cigarette": 150
  }
}
```

### 5.8 获取快速统计

**端点:** `GET /api/v1/projects/{project_id}/datasets/quick-stats`

**响应:** `200 OK`
```json
{
  "total_datasets": 5,
  "latest_version": "v1.4",
  "total_size_gb": 2.3
}
```

---

## 6. 训练管理 API

集成 Ultralytics YOLO 官方库，支持 YOLOv8 和 YOLOv11 全系列模型训练。

### 6.1 创建训练任务

**端点:** `POST /api/v1/projects/{project_id}/training/tasks`

**请求体:**
```json
{
  "task_name": "yolov8_baseline",
  "dataset_version_id": 789,
  "yolo_version": "yolov8",
  "model_size": "n",
  "pretrained": true,
  "epochs": 100,
  "batch_size": 16,
  "img_size": 640,
  "learning_rate": 0.01,
  "patience": 50,
  "use_amp": true,
  "device": "0",
  "use_kfold": false
}
```

**或使用预设配置:**
```json
{
  "task_name": "quick_test",
  "dataset_version_id": 789,
  "preset": "quick"
}
```

**预设类型:**
- `quick`: 50 epochs, 快速测试
- `balanced`: 100 epochs, 推荐配置
- `high_accuracy`: 300 epochs, 高精度

**响应:** `201 Created`
```json
{
  "task_id": 1001,
  "status": "pending",
  "estimated_time": 3600
}
```

### 6.2 获取项目的训练任务列表

**端点:** `GET /api/v1/projects/{project_id}/training/tasks`

**查询参数:**
- `page` (int) - 页码
- `per_page` (int) - 每页数量
- `status` (string, 可选) - 过滤状态

**响应:** `200 OK`

### 6.3 获取训练任务详情

**端点:** `GET /api/v1/projects/{project_id}/training/tasks/{task_id}`

**响应:** `200 OK`
```json
{
  "task_id": 1001,
  "task_name": "yolov8_baseline",
  "status": "running",
  "progress": 35,
  "current_epoch": 35,
  "total_epochs": 100,
  "current_metrics": {
    "train_loss": 0.023,
    "val_loss": 0.028,
    "precision": 0.85,
    "recall": 0.82,
    "mAP50": 0.88,
    "mAP50_95": 0.65
  },
  "best_metrics": {
    "epoch": 28,
    "mAP50": 0.89,
    "mAP50_95": 0.67
  },
  "elapsed_time": 2100,
  "estimated_remaining": 3900,
  "gpu_info": {
    "device": "NVIDIA RTX 4090",
    "memory_used_mb": 18500,
    "memory_total_mb": 24576,
    "temperature_c": 72,
    "power_usage_w": 280
  }
}
```

### 6.4 停止训练任务

**端点:** `POST /api/v1/projects/{project_id}/training/tasks/{task_id}/stop`

**响应:** `200 OK`
```json
{
  "message": "Training task stopped",
  "current_epoch": 45
}
```

### 6.5 删除训练任务

**端点:** `DELETE /api/v1/projects/{project_id}/training/tasks/{task_id}`

**响应:** `204 No Content`

### 6.6 获取项目的所有模型

**端点:** `GET /api/v1/projects/{project_id}/models`

**查询参数:**
- `sort_by` (string) - created_at, mAP50, mAP50_95
- `order` (string) - asc, desc

**响应:** `200 OK`
```json
{
  "total": 5,
  "models": [
    {
      "id": 2001,
      "name": "smoking_detector_v1",
      "model_version": "1.0",
      "training_task_id": 1001,
      "yolo_version": "yolov8",
      "model_size": "n",
      "model_path": "/path/to/best.pt",
      "model_size_mb": 6.2,
      "metrics": {
        "mAP50": 0.89,
        "mAP50_95": 0.67,
        "precision": 0.86,
        "recall": 0.83
      },
      "inference_time_ms": 14.7,
      "is_best": true,
      "is_deployed": true,
      "created_at": "2025-11-09T15:00:00Z"
    }
  ]
}
```

### 6.7 获取模型详情

**端点:** `GET /api/v1/projects/{project_id}/models/{model_id}`

**响应:** `200 OK`
```json
{
  "id": 2001,
  "name": "smoking_detector_v1",
  "yolo_version": "yolov8n",
  "training_task_id": 1001,
  "metrics": {
    "mAP50": 0.89,
    "mAP50_95": 0.67,
    "precision": 0.86,
    "recall": 0.83
  },
  "model_path": "/path/to/best.pt",
  "model_size_mb": 6.2,
  "created_at": "2025-11-09T15:00:00Z"
}
```

### 6.8 获取训练超参数预设

**端点:** `GET /api/v1/training/hyperparameters/presets`

**响应:** `200 OK`
```json
{
  "presets": [
    {
      "name": "default",
      "description": "Default training configuration",
      "params": {
        "epochs": 100,
        "batch_size": 16,
        "lr0": 0.01
      }
    },
    {
      "name": "fast",
      "description": "Quick training for testing",
      "params": {
        "epochs": 50,
        "batch_size": 32
      }
    },
    {
      "name": "accurate",
      "description": "High accuracy training",
      "params": {
        "epochs": 300,
        "batch_size": 8
      }
    },
    {
      "name": "augmented",
      "description": "Training with heavy augmentation",
      "params": {
        "mosaic": 1.0,
        "mixup": 0.5
      }
    }
  ]
}
```

---

## 附录

### 支持的 YOLO 模型版本

```python
YOLOv8: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
YOLOv11: yolov11n, yolov11s, yolov11m, yolov11l, yolov11x
```

### 坐标系统说明

**Qwen格式** (0-1000):
```
bbox: [x1, y1, x2, y2]  # 归一化到 0-1000 范围
```

**YOLO格式** (0-1):
```
bbox: [center_x, center_y, width, height]  # 归一化到 0-1 范围
```

**COCO格式** (像素):
```
bbox: [x, y, width, height]  # 左上角坐标 + 宽高(像素)
```

### 旧版本兼容性端点 (已移除)

以下端点在旧版本文档中存在，但未在当前版本实现：

- 模型推理 (单张预测) - 计划在 Phase 13 实现
- 模型评估 - 计划在 Phase 13 实现
- 模型部署 - 计划在 Phase 13 实现
- 健康检查 - 计划在 Phase 10 实现
- WebSocket 实时更新 - 计划在 Phase 8 实现

---

**文档版本:** v1.0
**最后更新:** 2025-11-09
**对应后端版本:** Phases 1-7 完成

---


## 错误响应

所有API在出错时返回统一格式：

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project with id 999 not found",
    "details": {},
    "timestamp": "2025-11-09T16:00:00Z"
  }
}
```

**常见错误码:**
- `RESOURCE_NOT_FOUND` (404)
- `VALIDATION_ERROR` (422)
- `INTERNAL_SERVER_ERROR` (500)
- `TASK_ALREADY_RUNNING` (409)
- `INSUFFICIENT_RESOURCES` (503)

---

## 分页响应格式

所有列表API使用统一分页格式：

```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5,
  "items": [...]
}
```

---

## 速率限制

暂无速率限制 (MVP版本)

未来版本可能添加:
- 每IP每分钟60次请求
- 图片生成API: 每小时100张
