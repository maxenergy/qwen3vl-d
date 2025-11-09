"""
训练相关的Celery任务
Training Celery Tasks
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from celery import Task

from backend.celery_app import celery_app
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.core.logging import logger
from backend.models.training import TrainingTask, Model as TrainedModel
from backend.models.dataset import DatasetVersion
from backend.services.yolo_trainer import YOLOTrainer


class DatabaseTask(Task):
    """带数据库会话的任务基类"""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """任务完成后关闭数据库连接"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.training.execute_training_task")
def execute_training_task(self, task_id: int):
    """
    执行训练任务

    Args:
        task_id: 训练任务ID
    """
    task = self.db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

    if not task:
        logger.error(f"Training task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    try:
        # 更新状态为运行中
        task.status = "running"
        task.started_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Starting training task {task_id}")

        # 获取数据集
        dataset = (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.id == task.dataset_id)
            .first()
        )

        if not dataset or dataset.status != "completed":
            raise ValueError("Dataset not ready for training")

        # 获取超参数
        hyperparams = task.hyperparameters or {}

        # 创建训练器
        trainer = YOLOTrainer(
            model_version=task.model_version,
            pretrained=hyperparams.get("pretrained", True),
            device=hyperparams.get("device", "0"),
        )

        # 准备训练目录
        output_dir = os.path.join(
            str(settings.data_dir),
            "training",
            str(task.project_id),
            f"task_{task_id}",
        )
        os.makedirs(output_dir, exist_ok=True)

        # 数据集配置文件
        data_yaml = os.path.join(dataset.output_path, "data.yaml")
        if not os.path.exists(data_yaml):
            raise FileNotFoundError(f"Dataset config not found: {data_yaml}")

        # 准备训练参数
        train_args = {
            "data_yaml": data_yaml,
            "epochs": hyperparams.get("epochs", 100),
            "batch_size": hyperparams.get("batch_size", 16),
            "imgsz": hyperparams.get("imgsz", 640),
            "save_dir": output_dir,
            "name": task.name or f"task_{task_id}",
            "resume": hyperparams.get("resume", False),
            "optimizer": hyperparams.get("optimizer", "auto"),
            "lr0": hyperparams.get("lr0", 0.01),
            "lrf": hyperparams.get("lrf", 0.01),
            "momentum": hyperparams.get("momentum", 0.937),
            "weight_decay": hyperparams.get("weight_decay", 0.0005),
            "warmup_epochs": hyperparams.get("warmup_epochs", 3.0),
            "patience": hyperparams.get("patience", 100),
        }

        logger.info(f"Training with args: {train_args}")

        # 训练进度回调
        def progress_callback(info):
            """训练进度回调"""
            if "epoch" in info and "total_epochs" in info:
                progress = int((info["epoch"] / info["total_epochs"]) * 100)
                task.progress = progress
                self.db.commit()

                # 更新Celery任务状态
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current_epoch": info["epoch"],
                        "total_epochs": info["total_epochs"],
                        "progress": progress,
                    },
                )

        # 开始训练
        results = trainer.train(**train_args, callback=progress_callback)

        # 保存结果
        task.output_dir = output_dir
        task.metrics = results.get("metrics", {})
        task.progress = 100

        # 查找最佳模型
        best_model_path = results.get("best_model")
        if best_model_path and os.path.exists(best_model_path):
            # 创建模型记录
            model = TrainedModel(
                project_id=task.project_id,
                training_task_id=task.id,
                dataset_id=task.dataset_id,
                name=f"{task.name}_best",
                version=task.model_version,
                model_path=best_model_path,
                metrics=task.metrics,
                hyperparameters=task.hyperparameters,
            )
            self.db.add(model)

        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Training task {task_id} completed successfully")

        return {
            "status": "completed",
            "task_id": task_id,
            "metrics": task.metrics,
            "output_dir": output_dir,
            "best_model": best_model_path,
        }

    except Exception as e:
        logger.error(f"Training task {task_id} failed: {e}")
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.training.validate_model")
def validate_model(self, model_id: int, split: str = "val"):
    """
    验证模型

    Args:
        model_id: 模型ID
        split: 数据集分割 (val, test)
    """
    model = self.db.query(TrainedModel).filter(TrainedModel.id == model_id).first()

    if not model:
        logger.error(f"Model {model_id} not found")
        return {"status": "error", "message": "Model not found"}

    try:
        logger.info(f"Validating model {model_id} on {split} split")

        # 获取数据集
        dataset = (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.id == model.dataset_id)
            .first()
        )

        if not dataset:
            raise ValueError("Dataset not found")

        # 创建训练器并加载模型
        trainer = YOLOTrainer()
        trainer.load_checkpoint(model.model_path)

        # 数据集配置
        data_yaml = os.path.join(dataset.output_path, "data.yaml")

        # 验证
        val_results = trainer.validate(
            data_yaml=data_yaml,
            split=split,
        )

        # 更新模型指标
        val_metrics = val_results.get("metrics", {})
        if model.metrics:
            model.metrics.update({f"{split}_{k}": v for k, v in val_metrics.items()})
        else:
            model.metrics = {f"{split}_{k}": v for k, v in val_metrics.items()}

        self.db.commit()

        logger.info(f"Model validation completed: {val_metrics}")

        return {
            "status": "completed",
            "model_id": model_id,
            "split": split,
            "metrics": val_metrics,
        }

    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return {
            "status": "failed",
            "model_id": model_id,
            "error": str(e),
        }


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.training.export_model")
def export_model(
    self,
    model_id: int,
    format: str = "onnx",
    optimize: bool = True,
    half: bool = False,
):
    """
    导出模型

    Args:
        model_id: 模型ID
        format: 导出格式 (onnx, torchscript, tflite, etc.)
        optimize: 是否优化
        half: 是否使用FP16
    """
    model = self.db.query(TrainedModel).filter(TrainedModel.id == model_id).first()

    if not model:
        logger.error(f"Model {model_id} not found")
        return {"status": "error", "message": "Model not found"}

    try:
        logger.info(f"Exporting model {model_id} to {format}")

        # 创建训练器并加载模型
        trainer = YOLOTrainer()
        trainer.load_checkpoint(model.model_path)

        # 导出
        export_path = trainer.export(
            format=format,
            optimize=optimize,
            half=half,
        )

        logger.info(f"Model exported to {export_path}")

        # 更新模型记录
        if not hasattr(model, "exported_formats"):
            model.exported_formats = {}

        model.exported_formats[format] = export_path
        self.db.commit()

        return {
            "status": "completed",
            "model_id": model_id,
            "format": format,
            "export_path": export_path,
        }

    except Exception as e:
        logger.error(f"Model export failed: {e}")
        return {
            "status": "failed",
            "model_id": model_id,
            "error": str(e),
        }


@celery_app.task(name="backend.tasks.training.cleanup_old_training_outputs")
def cleanup_old_training_outputs(days: int = 30):
    """
    清理旧的训练输出文件

    Args:
        days: 清理多少天之前的文件
    """
    db = SessionLocal()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 查找旧训练任务
        old_tasks = (
            db.query(TrainingTask)
            .filter(
                TrainingTask.status.in_(["completed", "failed", "stopped"]),
                TrainingTask.completed_at < cutoff_date,
            )
            .all()
        )

        cleaned = 0
        for task in old_tasks:
            try:
                if task.output_dir and os.path.exists(task.output_dir):
                    shutil.rmtree(task.output_dir)
                    logger.info(f"Cleaned up training output {task.id} at {task.output_dir}")
                    cleaned += 1
            except Exception as e:
                logger.error(f"Failed to cleanup training {task.id}: {e}")

        logger.info(f"Cleaned up {cleaned} old training outputs (older than {days} days)")

        return {
            "status": "success",
            "cleaned": cleaned,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old training outputs: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()
