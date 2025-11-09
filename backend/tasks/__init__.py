"""
Celery任务模块
Celery Tasks Module

包含所有异步任务定义
"""

from backend.tasks import generation, maintenance

__all__ = [
    "generation",
    "maintenance",
]
