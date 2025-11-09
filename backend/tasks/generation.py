"""
图片生成相关的Celery任务
Image Generation Celery Tasks
"""

import os
from datetime import datetime
from typing import Optional

from celery import Task

from backend.celery_app import celery_app
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.core.logging import logger
from backend.models.generation import GenerationTask, Image as ImageModel
from backend.services.hunyuan_generator import HunyuanImageGenerator


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


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.generation.execute_generation_task")
def execute_generation_task(self, task_id: int):
    """
    执行图片生成任务

    Args:
        task_id: 生成任务ID
    """
    task = self.db.query(GenerationTask).filter(GenerationTask.id == task_id).first()

    if not task:
        logger.error(f"Generation task {task_id} not found")
        return {"status": "error", "message": "Task not found"}

    try:
        # 更新状态为处理中
        task.status = "processing"
        task.started_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Starting generation task {task_id}")

        # 创建生成器
        generator = HunyuanImageGenerator(
            api_url=settings.hunyuan_api_url,
            use_local=False,  # 默认使用API模式
        )

        # 生成图片
        for i in range(task.batch_size):
            try:
                logger.info(f"Generating image {i+1}/{task.batch_size} for task {task_id}")

                # 更新进度
                progress = int((i / task.batch_size) * 100)
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i,
                        "total": task.batch_size,
                        "progress": progress,
                        "status": f"Generating image {i+1}/{task.batch_size}",
                    },
                )

                # 调用生成
                if task.mode == "text_to_image":
                    # 使用同步包装异步函数
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        image, params = loop.run_until_complete(
                            generator.generate_text_to_image(
                                prompt=task.prompt,
                                negative_prompt=task.negative_prompt,
                                resolution=task.resolution,
                                **(task.params or {}),
                            )
                        )
                    finally:
                        loop.close()
                else:
                    # TODO: 支持image_to_image模式
                    raise NotImplementedError("image_to_image mode not implemented yet")

                # 保存图片
                output_dir = os.path.join(
                    str(settings.data_dir),
                    "projects",
                    str(task.project_id),
                    "generated",
                )
                filename = f"task_{task_id}_{i+1}"

                # 使用同步包装
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    file_path = loop.run_until_complete(
                        generator.save_image(image, output_dir, filename)
                    )
                finally:
                    loop.close()

                # 创建图片记录
                image_record = ImageModel(
                    project_id=task.project_id,
                    generation_task_id=task.id,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    width=image.width,
                    height=image.height,
                    generation_params=params,
                    review_status="pending",
                )
                self.db.add(image_record)

                # 更新任务进度
                task.progress = int(((i + 1) / task.batch_size) * 100)
                self.db.commit()

                logger.info(f"Generated image {i+1}/{task.batch_size}: {file_path}")

            except Exception as e:
                logger.error(f"Failed to generate image {i+1}: {e}")
                # 继续生成下一张

        # 完成
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress = 100
        self.db.commit()

        logger.info(f"Generation task {task_id} completed")

        return {
            "status": "completed",
            "task_id": task_id,
            "images_generated": task.batch_size,
        }

    except Exception as e:
        logger.error(f"Generation task {task_id} failed: {e}")
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.generation.batch_generate")
def batch_generate(self, project_id: int, prompts: list, common_params: dict):
    """
    批量生成图片任务

    Args:
        project_id: 项目ID
        prompts: 提示词列表
        common_params: 公共参数
    """
    results = []

    for i, prompt in enumerate(prompts):
        try:
            # 创建生成任务
            task = GenerationTask(
                project_id=project_id,
                name=f"Batch_{i+1}",
                prompt=prompt,
                negative_prompt=common_params.get("negative_prompt", ""),
                mode=common_params.get("mode", "text_to_image"),
                resolution=common_params.get("resolution", "1024x1024"),
                batch_size=1,
                params=common_params.get("params", {}),
                status="pending",
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            # 提交生成任务
            execute_generation_task.delay(task.id)

            results.append({
                "task_id": task.id,
                "prompt": prompt,
                "status": "submitted",
            })

        except Exception as e:
            logger.error(f"Failed to create batch task {i}: {e}")
            results.append({
                "prompt": prompt,
                "status": "failed",
                "error": str(e),
            })

    return {
        "total": len(prompts),
        "results": results,
    }


@celery_app.task(name="backend.tasks.generation.cancel_generation_task")
def cancel_generation_task(task_id: int):
    """
    取消生成任务

    Args:
        task_id: 任务ID
    """
    db = SessionLocal()
    try:
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()

        if not task:
            logger.error(f"Generation task {task_id} not found")
            return {"status": "error", "message": "Task not found"}

        if task.status not in ["pending", "processing"]:
            logger.warning(f"Cannot cancel task {task_id} with status {task.status}")
            return {"status": "error", "message": f"Cannot cancel task with status {task.status}"}

        # 更新状态
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Cancelled generation task {task_id}")

        return {"status": "success", "task_id": task_id}

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()
