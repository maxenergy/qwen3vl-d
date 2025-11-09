"""
标注相关的Celery任务
Annotation Celery Tasks
"""

import os
from datetime import datetime
from typing import List

from celery import Task
from PIL import Image

from backend.celery_app import celery_app
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.core.logging import logger
from backend.models.annotation import AnnotationTask, Annotation
from backend.models.generation import Image as ImageModel
from backend.models.project import Label
from backend.services.qwen3vl_detector import Qwen3VLClient


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


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.annotation.execute_annotation_task")
def execute_annotation_task(self, task_id: int):
    """
    执行标注任务

    Args:
        task_id: 标注任务ID
    """
    task = self.db.query(AnnotationTask).filter(AnnotationTask.id == task_id).first()

    if not task:
        logger.error(f"Annotation task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    try:
        # 更新状态为处理中
        task.status = "processing"
        task.started_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Starting annotation task {task_id}")

        # 获取图片和标签
        images = (
            self.db.query(ImageModel)
            .filter(ImageModel.id.in_(task.image_ids))
            .all()
        )

        labels = (
            self.db.query(Label)
            .filter(Label.id.in_(task.label_ids))
            .all()
        )

        if not images:
            raise ValueError("No images found for this task")

        if not labels:
            raise ValueError("No labels found for this task")

        # 构建标签名称列表
        label_names = [label.name for label in labels]
        label_id_map = {label.name: label.id for label in labels}

        # 创建Qwen3-VL客户端
        client = Qwen3VLClient()

        # 获取模型配置
        model_config = task.model_config or {}
        confidence_threshold = model_config.get("confidence_threshold", 0.5)
        prompt_template = model_config.get("prompt_template")

        # 处理每张图片
        total_annotations = 0
        for i, image_record in enumerate(images):
            try:
                logger.info(f"Annotating image {i+1}/{len(images)}: {image_record.id}")

                # 更新进度
                progress = int((i / len(images)) * 100)
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i,
                        "total": len(images),
                        "progress": progress,
                        "status": f"Annotating image {i+1}/{len(images)}",
                    },
                )

                # 加载图片
                if not os.path.exists(image_record.file_path):
                    logger.warning(f"Image file not found: {image_record.file_path}")
                    continue

                pil_image = Image.open(image_record.file_path)

                # 使用同步包装异步函数
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    detection_result = loop.run_until_complete(
                        client.detect_objects(
                            image=pil_image,
                            labels=label_names,
                            prompt_template=prompt_template,
                            confidence_threshold=confidence_threshold,
                        )
                    )
                finally:
                    loop.close()

                # 保存检测结果
                for bbox in detection_result.bboxes:
                    # 获取标签ID
                    label_id = label_id_map.get(bbox.label)
                    if not label_id:
                        logger.warning(f"Label not found: {bbox.label}")
                        continue

                    # 创建标注记录
                    annotation = Annotation(
                        project_id=task.project_id,
                        image_id=image_record.id,
                        annotation_task_id=task.id,
                        label_id=label_id,
                        x_min=bbox.x_min,
                        y_min=bbox.y_min,
                        x_max=bbox.x_max,
                        y_max=bbox.y_max,
                        confidence=bbox.confidence,
                        review_status="pending",
                    )
                    self.db.add(annotation)
                    total_annotations += 1

                # 更新任务进度
                task.progress = int(((i + 1) / len(images)) * 100)
                self.db.commit()

                logger.info(f"Annotated image {i+1}/{len(images)}: found {len(detection_result)} objects")

            except Exception as e:
                logger.error(f"Failed to annotate image {image_record.id}: {e}")
                # 继续处理下一张

        # 完成
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress = 100
        self.db.commit()

        logger.info(f"Annotation task {task_id} completed: {total_annotations} annotations created")

        # 关闭客户端
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(client.close())
        finally:
            loop.close()

        return {
            "status": "completed",
            "task_id": task_id,
            "total_annotations": total_annotations,
            "images_processed": len(images),
        }

    except Exception as e:
        logger.error(f"Annotation task {task_id} failed: {e}")
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.annotation.batch_annotate_images")
def batch_annotate_images(self, project_id: int, image_ids: List[int], label_ids: List[int], config: dict):
    """
    批量标注图片任务

    Args:
        project_id: 项目ID
        image_ids: 图片ID列表
        label_ids: 标签ID列表
        config: 配置参数
    """
    try:
        # 创建标注任务
        task = AnnotationTask(
            project_id=project_id,
            name=config.get("name", "Batch Annotation"),
            description=config.get("description"),
            model_config={
                "model": config.get("model", "qwen3-vl-30b"),
                "confidence_threshold": config.get("confidence_threshold", 0.5),
                "prompt_template": config.get("prompt_template"),
            },
            status="pending",
        )

        self.db.add(task)
        self.db.flush()

        # 关联图片和标签
        task.image_ids = image_ids
        task.label_ids = label_ids

        self.db.commit()
        self.db.refresh(task)

        # 执行标注任务
        result = execute_annotation_task(task.id)

        return result

    except Exception as e:
        logger.error(f"Failed to batch annotate: {e}")
        self.db.rollback()
        return {"status": "error", "error": str(e)}


@celery_app.task(name="backend.tasks.annotation.cancel_annotation_task")
def cancel_annotation_task(task_id: int):
    """
    取消标注任务

    Args:
        task_id: 任务ID
    """
    db = SessionLocal()
    try:
        task = db.query(AnnotationTask).filter(AnnotationTask.id == task_id).first()

        if not task:
            logger.error(f"Annotation task {task_id} not found")
            return {"status": "error", "message": "Task not found"}

        if task.status not in ["pending", "processing"]:
            logger.warning(f"Cannot cancel task {task_id} with status {task.status}")
            return {"status": "error", "message": f"Cannot cancel task with status {task.status}"}

        # 更新状态
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Cancelled annotation task {task_id}")

        return {"status": "success", "task_id": task_id}

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.annotation.re_annotate_by_label")
def re_annotate_by_label(self, project_id: int, label_id: int, image_ids: List[int]):
    """
    重新标注指定标签的图片

    Args:
        project_id: 项目ID
        label_id: 标签ID
        image_ids: 图片ID列表
    """
    try:
        # 删除旧标注
        count = (
            self.db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.label_id == label_id,
                Annotation.image_id.in_(image_ids),
            )
            .delete(synchronize_session=False)
        )

        self.db.commit()

        logger.info(f"Deleted {count} old annotations for label {label_id}")

        # 创建新的标注任务
        task = AnnotationTask(
            project_id=project_id,
            name=f"Re-annotate Label {label_id}",
            description=f"Re-annotation for label {label_id}",
            model_config={
                "model": "qwen3-vl-30b",
                "confidence_threshold": 0.5,
            },
            status="pending",
        )

        self.db.add(task)
        self.db.flush()

        # 关联图片和标签
        task.image_ids = image_ids
        task.label_ids = [label_id]

        self.db.commit()
        self.db.refresh(task)

        # 执行标注
        result = execute_annotation_task(task.id)

        return result

    except Exception as e:
        logger.error(f"Failed to re-annotate: {e}")
        self.db.rollback()
        return {"status": "error", "error": str(e)}
