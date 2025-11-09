"""
训练API路由
Training API Routes

YOLO模型训练任务管理
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.api.dependencies import (
    get_db_session,
    get_project_or_404,
    get_pagination_params,
)
from backend.core.logging import logger
from backend.models.project import Project
from backend.models.dataset import DatasetVersion
from backend.models.training import TrainingTask, Model as TrainedModel
from backend.schemas.training import (
    TrainingTaskCreate,
    TrainingTaskResponse,
    TrainingTaskListItem,
    TrainingStopRequest,
    ModelResponse,
)
from backend.schemas.common import PagedResponse


router = APIRouter()


@router.post("/projects/{project_id}/training/tasks", status_code=201)
async def create_training_task(
    project_id: int,
    task_data: TrainingTaskCreate,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> TrainingTaskResponse:
    """
    创建训练任务

    - **project_id**: 项目ID
    - **task_data**: 训练配置
    """
    try:
        # 验证数据集存在且已完成
        dataset = (
            db.query(DatasetVersion)
            .filter(
                DatasetVersion.id == task_data.dataset_id,
                DatasetVersion.project_id == project_id,
            )
            .first()
        )

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        if dataset.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Dataset status is {dataset.status}, must be completed",
            )

        if dataset.format != "yolo":
            raise HTTPException(
                status_code=400,
                detail=f"Only YOLO format supported for training, got {dataset.format}",
            )

        # 创建训练任务
        task = TrainingTask(
            project_id=project_id,
            dataset_id=task_data.dataset_id,
            name=task_data.name,
            description=task_data.description,
            model_version=task_data.model_version,
            hyperparameters={
                "epochs": task_data.epochs,
                "batch_size": task_data.batch_size,
                "imgsz": task_data.imgsz,
                "optimizer": task_data.optimizer,
                "lr0": task_data.lr0,
                "lrf": task_data.lrf,
                "momentum": task_data.momentum,
                "weight_decay": task_data.weight_decay,
                "warmup_epochs": task_data.warmup_epochs,
                "patience": task_data.patience,
                "device": task_data.device or "0",
                "pretrained": task_data.pretrained,
                "resume": task_data.resume,
            },
            status="pending",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"Created training task {task.id} for project {project_id}")

        # 使用Celery异步执行训练
        from backend.tasks.training import execute_training_task
        execute_training_task.delay(task.id)

        return TrainingTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create training task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/projects/{project_id}/training/tasks")
async def list_training_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[TrainingTaskListItem]:
    """
    列出项目的训练任务

    - **project_id**: 项目ID
    - **status**: 状态筛选 (pending, running, completed, failed, stopped)
    """
    try:
        query = db.query(TrainingTask).filter(TrainingTask.project_id == project_id)

        # 状态筛选
        if status:
            query = query.filter(TrainingTask.status == status)

        # 总数
        total = query.count()

        # 分页查询
        tasks = (
            query.order_by(desc(TrainingTask.created_at))
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [TrainingTaskListItem.model_validate(task) for task in tasks]

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list training tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/training/tasks/{task_id}")
async def get_training_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> TrainingTaskResponse:
    """
    获取训练任务详情

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(TrainingTask)
        .filter(
            TrainingTask.id == task_id,
            TrainingTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")

    return TrainingTaskResponse.model_validate(task)


@router.post("/projects/{project_id}/training/tasks/{task_id}/stop")
async def stop_training_task(
    project_id: int,
    task_id: int,
    stop_data: TrainingStopRequest,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> TrainingTaskResponse:
    """
    停止训练任务

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(TrainingTask)
        .filter(
            TrainingTask.id == task_id,
            TrainingTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")

    if task.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop task with status {task.status}",
        )

    try:
        # 更新状态
        task.status = "stopped"
        task.completed_at = datetime.utcnow()
        task.error_message = stop_data.reason if stop_data.reason else "Manually stopped"

        db.commit()
        db.refresh(task)

        logger.info(f"Stopped training task {task_id}")

        # TODO: 实际停止Celery任务

        return TrainingTaskResponse.model_validate(task)

    except Exception as e:
        logger.error(f"Failed to stop training task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/training/tasks/{task_id}", status_code=204)
async def delete_training_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除训练任务

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(TrainingTask)
        .filter(
            TrainingTask.id == task_id,
            TrainingTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")

    if task.status in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete task in progress",
        )

    try:
        # 删除训练输出文件
        import shutil
        if task.output_dir and os.path.exists(task.output_dir):
            shutil.rmtree(task.output_dir)
            logger.info(f"Deleted training files at {task.output_dir}")

        db.delete(task)
        db.commit()

        logger.info(f"Deleted training task {task_id}")

    except Exception as e:
        logger.error(f"Failed to delete training task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/models")
async def list_trained_models(
    project_id: int,
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[ModelResponse]:
    """
    列出项目的训练模型

    - **project_id**: 项目ID
    """
    try:
        query = db.query(TrainedModel).filter(TrainedModel.project_id == project_id)

        # 总数
        total = query.count()

        # 分页查询
        models = (
            query.order_by(desc(TrainedModel.created_at))
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [ModelResponse.model_validate(model) for model in models]

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/models/{model_id}")
async def get_model(
    project_id: int,
    model_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> ModelResponse:
    """
    获取模型详情

    - **project_id**: 项目ID
    - **model_id**: 模型ID
    """
    model = (
        db.query(TrainedModel)
        .filter(
            TrainedModel.id == model_id,
            TrainedModel.project_id == project_id,
        )
        .first()
    )

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelResponse.model_validate(model)


@router.get("/training/hyperparameters/presets")
async def get_hyperparameter_presets() -> dict:
    """
    获取超参数预设

    返回可用的训练超参数预设配置
    """
    from backend.services.yolo_trainer import YOLOTrainer

    presets = {}
    for preset_name in ["default", "fast", "accurate", "augmented"]:
        presets[preset_name] = YOLOTrainer.get_training_hyperparameters(preset_name)

    return {
        "presets": presets,
        "descriptions": {
            "default": "平衡的训练配置，适合大多数场景",
            "fast": "快速训练，适合快速验证和原型",
            "accurate": "高精度训练，更多轮数和更高分辨率",
            "augmented": "强数据增强，适合小数据集",
        },
    }


import os

# Note: Training execution has been moved to backend/tasks/training.py
# using Celery for better scalability and reliability
