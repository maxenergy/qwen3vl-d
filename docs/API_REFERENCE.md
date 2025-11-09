# API接口文档

## 基础信息

**Base URL:** `http://localhost:8000/api/v1`
**认证方式:** 暂不需要 (MVP版本)
**内容类型:** `application/json`
**字符编码:** `UTF-8`

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

## 3. 图片生成 API

### 3.1 创建生成任务

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

### 3.2 获取生成任务状态

**端点:** `GET /api/v1/generation/tasks/{task_id}`

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

### 3.3 获取生成的图片列表

**端点:** `GET /api/v1/generation/tasks/{task_id}/images`

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

### 3.4 审核图片

**端点:** `POST /api/v1/images/{image_id}/review`

**请求体:**
```json
{
  "status": "approved",
  "notes": "Good quality image"
}
```

**响应:** `200 OK`

### 3.5 批量审核

**端点:** `POST /api/v1/images/batch-review`

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

### 3.6 任务控制

**暂停任务:** `POST /api/v1/generation/tasks/{task_id}/pause`
**恢复任务:** `POST /api/v1/generation/tasks/{task_id}/resume`
**取消任务:** `POST /api/v1/generation/tasks/{task_id}/cancel`

**响应:** `200 OK`

### 3.7 获取提示词模板

**端点:** `GET /api/v1/templates/prompts`

**响应:** `200 OK`
```json
{
  "categories": [
    {
      "name": "traffic",
      "display_name": "交通场景",
      "templates": [
        {
          "id": "traffic_smoking",
          "name": "交通场景-吸烟检测",
          "template": "A {time} photo of {location} with smoking people...",
          "variables": {
            "time": {
              "type": "enum",
              "options": ["daytime", "night", "dusk"]
            },
            "location": {
              "type": "enum",
              "options": ["street", "park", "bus stop"]
            }
          }
        }
      ]
    }
  ]
}
```

---

## 4. 自动标注 API

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

### 4.2 获取标注任务状态

**端点:** `GET /api/v1/annotation/tasks/{task_id}`

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

### 4.3 获取标注结果

**端点:** `GET /api/v1/annotation/tasks/{task_id}/results`

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

### 4.4 校验标注

**端点:** `POST /api/v1/annotations/{annotation_id}/verify`

**请求体:**
```json
{
  "is_correct": true,
  "correction_bbox": [105, 205, 305, 405],
  "notes": "Slightly adjusted bbox"
}
```

**响应:** `200 OK`

### 4.5 批量校验

**端点:** `POST /api/v1/annotations/batch-verify`

**请求体:**
```json
{
  "annotation_ids": [5001, 5002, 5003],
  "is_correct": true
}
```

**响应:** `200 OK`

### 4.6 删除某类别所有标注

**端点:** `DELETE /api/v1/annotation/tasks/{task_id}/labels/{label_name}`

**响应:** `200 OK`
```json
{
  "deleted_count": 50,
  "message": "All annotations for 'cigarette' have been deleted"
}
```

### 4.7 重新标注

**端点:** `POST /api/v1/annotation/tasks/{task_id}/re-annotate`

**请求体:**
```json
{
  "label_names": ["cigarette"],
  "image_ids": "all",
  "confidence_threshold": 0.5
}
```

**响应:** `201 Created`
```json
{
  "new_task_id": 457
}
```

---

## 5. 数据集管理 API

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

**端点:** `GET /api/v1/datasets/{version_id}`

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

### 5.4 下载数据集

**端点:** `GET /api/v1/datasets/{version_id}/download/{format}`

**路径参数:**
- `format`: `yolo` 或 `coco`

**响应:** `200 OK` (文件下载)
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="smoking_detection_v1.0_yolo.zip"`

### 5.5 生成K-Fold数据集

**端点:** `POST /api/v1/datasets/{version_id}/generate-kfold`

**请求体:**
```json
{
  "n_splits": 5,
  "shuffle": true,
  "random_seed": 42
}
```

**响应:** `200 OK`
```json
{
  "message": "K-Fold datasets generated successfully",
  "folds": 5,
  "output_dir": "/path/to/datasets/v1.0/kfold"
}
```

---

## 6. 训练管理 API

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

### 6.2 获取训练任务状态

**端点:** `GET /api/v1/training/tasks/{task_id}`

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

### 6.3 获取训练日志 (实时流)

**端点:** `GET /api/v1/training/tasks/{task_id}/logs`

**响应:** Server-Sent Events (SSE)
```
data: {"epoch": 35, "batch": 10, "loss": 0.023}

data: {"epoch": 35, "batch": 11, "loss": 0.022}
```

### 6.4 获取TensorBoard URL

**端点:** `GET /api/v1/training/tasks/{task_id}/tensorboard`

**响应:** `200 OK`
```json
{
  "url": "http://localhost:6006",
  "is_running": true,
  "log_dir": "/path/to/runs/run_001"
}
```

### 6.5 训练控制

**停止训练:** `POST /api/v1/training/tasks/{task_id}/stop`

**响应:** `200 OK`

### 6.6 获取训练结果

**端点:** `GET /api/v1/training/tasks/{task_id}/results`

**响应:** `200 OK`
```json
{
  "task_id": 1001,
  "status": "completed",
  "total_epochs": 100,
  "best_epoch": 67,
  "training_time_seconds": 5832,
  "final_metrics": {
    "mAP50": 0.89,
    "mAP50_95": 0.67,
    "precision": 0.86,
    "recall": 0.83
  },
  "per_class_metrics": {
    "smoking_person": {
      "precision": 0.88,
      "recall": 0.85,
      "mAP50": 0.90,
      "mAP50_95": 0.70
    },
    "cigarette": {
      "precision": 0.84,
      "recall": 0.81,
      "mAP50": 0.87,
      "mAP50_95": 0.64
    }
  },
  "model_path": "/path/to/weights/best.pt",
  "model_size_mb": 6.2,
  "charts": {
    "confusion_matrix": "/api/v1/training/1001/charts/confusion_matrix.png",
    "results_curve": "/api/v1/training/1001/charts/results.png",
    "pr_curve": "/api/v1/training/1001/charts/PR_curve.png",
    "f1_curve": "/api/v1/training/1001/charts/F1_curve.png"
  }
}
```

### 6.7 获取图表

**端点:** `GET /api/v1/training/{task_id}/charts/{chart_name}`

**路径参数:**
- `chart_name`: confusion_matrix, results, PR_curve, F1_curve

**响应:** `200 OK` (图片文件)

---

## 7. 模型管理 API

### 7.1 获取模型列表

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

### 7.2 获取模型详情

**端点:** `GET /api/v1/models/{model_id}`

**响应:** `200 OK`

### 7.3 模型推理 (单张预测)

**端点:** `POST /api/v1/models/{model_id}/predict`

**请求:** multipart/form-data
- `image`: 图片文件
- `confidence`: (可选) 置信度阈值, 默认0.5
- `iou`: (可选) IoU阈值, 默认0.45

**响应:** `200 OK`
```json
{
  "predictions": [
    {
      "label": "smoking_person",
      "bbox": [100, 200, 300, 400],
      "confidence": 0.91
    },
    {
      "label": "cigarette",
      "bbox": [250, 350, 280, 380],
      "confidence": 0.86
    }
  ],
  "prediction_count": 2,
  "visualization_url": "/api/v1/models/2001/predictions/latest.jpg",
  "inference_time_ms": 15.3
}
```

### 7.4 模型评估 (测试集)

**端点:** `POST /api/v1/models/{model_id}/evaluate`

**请求体:**
```json
{
  "dataset_version_id": 789,
  "split": "test"
}
```

**响应:** `200 OK`
```json
{
  "evaluation_id": 3001,
  "status": "completed",
  "metrics": {
    "mAP50": 0.88,
    "mAP50_95": 0.66,
    "precision": 0.874,
    "recall": 0.856
  },
  "per_class_metrics": {...},
  "confusion_matrix_url": "/api/v1/evaluations/3001/confusion_matrix.png"
}
```

### 7.5 标记为最佳模型

**端点:** `POST /api/v1/models/{model_id}/mark-best`

**响应:** `200 OK`

### 7.6 部署模型

**端点:** `POST /api/v1/models/{model_id}/deploy`

**响应:** `200 OK`
```json
{
  "message": "Model deployed successfully",
  "deployment_url": "/api/v1/predict"
}
```

---

## 8. 通用 API

### 8.1 健康检查

**端点:** `GET /api/v1/health`

**响应:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T16:00:00Z",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok",
    "hunyuan": "ok",
    "qwen3vl": "ok"
  },
  "version": "1.0.0"
}
```

### 8.2 系统统计

**端点:** `GET /api/v1/stats`

**响应:** `200 OK`
```json
{
  "projects": 5,
  "total_images": 5000,
  "total_annotations": 25000,
  "models_trained": 15,
  "disk_usage_gb": 45.2,
  "gpu_available": true
}
```

---

## 9. WebSocket API

### 9.1 任务实时更新

**端点:** `WS /api/v1/ws/tasks/{task_id}`

**消息格式 (服务器 → 客户端):**
```json
{
  "type": "progress_update",
  "task_type": "generation",
  "task_id": 123,
  "progress": 56,
  "message": "Generated 56/100 images",
  "timestamp": "2025-11-09T10:30:00Z"
}
```

**消息类型:**
- `progress_update` - 进度更新
- `status_change` - 状态变化
- `error` - 错误信息
- `completed` - 任务完成

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
