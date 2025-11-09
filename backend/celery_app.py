"""
Celery应用配置
Celery Application Configuration

配置Celery用于异步任务处理
"""

from celery import Celery
from celery.schedules import crontab

from backend.core.config import settings
from backend.core.logging import logger


# 创建Celery应用
celery_app = Celery(
    "auto_annotation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery配置
celery_app.conf.update(
    # 时区配置
    timezone="UTC",
    enable_utc=True,

    # 任务配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,  # 结果保留1小时

    # 任务执行配置
    task_track_started=True,
    task_time_limit=3600,  # 任务最长执行时间1小时
    task_soft_time_limit=3000,  # 软时间限制50分钟
    task_acks_late=True,  # 任务完成后才确认
    worker_prefetch_multiplier=1,  # 每次预取1个任务

    # 结果后端配置
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Worker配置
    worker_max_tasks_per_child=50,  # 每个worker最多执行50个任务后重启
    worker_disable_rate_limits=False,

    # 日志配置
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",

    # 任务路由
    task_routes={
        "backend.tasks.generation.*": {"queue": "generation"},
        "backend.tasks.annotation.*": {"queue": "annotation"},
        "backend.tasks.training.*": {"queue": "training"},
        "backend.tasks.dataset.*": {"queue": "dataset"},
    },

    # 定时任务（可选）
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "backend.tasks.maintenance.cleanup_old_tasks",
            "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
        },
        "check-stale-tasks": {
            "task": "backend.tasks.maintenance.check_stale_tasks",
            "schedule": 300.0,  # 每5分钟执行一次
        },
    },
)

# 自动发现任务
celery_app.autodiscover_tasks([
    "backend.tasks.generation",
    "backend.tasks.annotation",
    "backend.tasks.dataset",
    "backend.tasks.training",
    "backend.tasks.maintenance",
])


@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    logger.info(f"Request: {self.request!r}")
    return "OK"


if __name__ == "__main__":
    celery_app.start()
