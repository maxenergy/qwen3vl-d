"""
维护相关的Celery任务
Maintenance Celery Tasks

定期清理和检查任务
"""

from datetime import datetime, timedelta

from backend.celery_app import celery_app
from backend.core.database import SessionLocal
from backend.core.logging import logger
from backend.models.generation import GenerationTask
from backend.models.task_log import TaskLog


@celery_app.task(name="backend.tasks.maintenance.cleanup_old_tasks")
def cleanup_old_tasks(days: int = 30):
    """
    清理旧的已完成任务

    Args:
        days: 清理多少天之前的任务，默认30天
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 清理已完成的生成任务
        old_tasks = (
            db.query(GenerationTask)
            .filter(
                GenerationTask.status.in_(["completed", "failed", "cancelled"]),
                GenerationTask.completed_at < cutoff_date,
            )
            .all()
        )

        count = 0
        for task in old_tasks:
            # 删除关联的日志
            db.query(TaskLog).filter(
                TaskLog.task_type == "generation",
                TaskLog.task_id == task.id,
            ).delete()

            # 删除任务
            db.delete(task)
            count += 1

        db.commit()

        logger.info(f"Cleaned up {count} old tasks (older than {days} days)")

        return {
            "status": "success",
            "cleaned": count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old tasks: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="backend.tasks.maintenance.check_stale_tasks")
def check_stale_tasks(timeout_hours: int = 2):
    """
    检查并处理卡住的任务

    Args:
        timeout_hours: 超时时间（小时），默认2小时
    """
    db = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)

        # 查找处理中但很久没更新的任务
        stale_tasks = (
            db.query(GenerationTask)
            .filter(
                GenerationTask.status == "processing",
                GenerationTask.updated_at < cutoff_time,
            )
            .all()
        )

        count = 0
        for task in stale_tasks:
            logger.warning(f"Found stale task {task.id}, marking as failed")

            task.status = "failed"
            task.error_message = f"Task timed out after {timeout_hours} hours"
            task.completed_at = datetime.utcnow()
            count += 1

        db.commit()

        logger.info(f"Marked {count} stale tasks as failed")

        return {
            "status": "success",
            "stale_tasks": count,
            "timeout_hours": timeout_hours,
        }

    except Exception as e:
        logger.error(f"Failed to check stale tasks: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="backend.tasks.maintenance.disk_usage_report")
def disk_usage_report():
    """
    生成磁盘使用报告
    """
    db = SessionLocal()
    try:
        import os
        from backend.core.config import settings
        from backend.models.generation import Image as ImageModel

        # 统计各项目的磁盘使用
        projects_dir = os.path.join(str(settings.data_dir), "projects")

        if not os.path.exists(projects_dir):
            return {
                "status": "success",
                "message": "Projects directory does not exist",
            }

        project_stats = []

        for project_folder in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_folder)

            if not os.path.isdir(project_path):
                continue

            try:
                project_id = int(project_folder)

                # 计算目录大小
                total_size = 0
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(project_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
                            file_count += 1

                # 统计数据库中的图片数量
                image_count = (
                    db.query(ImageModel)
                    .filter(ImageModel.project_id == project_id)
                    .count()
                )

                project_stats.append({
                    "project_id": project_id,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "file_count": file_count,
                    "image_count": image_count,
                })

            except ValueError:
                # 不是项目文件夹
                continue

        # 计算总计
        total_size = sum(p["total_size_bytes"] for p in project_stats)
        total_files = sum(p["file_count"] for p in project_stats)

        logger.info(
            f"Disk usage: {len(project_stats)} projects, "
            f"{total_files} files, {round(total_size / (1024 * 1024), 2)} MB"
        )

        return {
            "status": "success",
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_files": total_files,
            "projects": project_stats,
        }

    except Exception as e:
        logger.error(f"Failed to generate disk usage report: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()
