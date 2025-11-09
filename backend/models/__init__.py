"""
数据模型包
Database Models Package

导入所有模型类，确保SQLAlchemy Base.metadata包含所有表定义
"""

from backend.core.database import Base

# 导入所有模型
from backend.models.project import Label, Project
from backend.models.dataset import DatasetVersion
from backend.models.generation import GenerationTask, Image
from backend.models.annotation import Annotation, AnnotationTask
from backend.models.training import Model, TrainingTask
from backend.models.task_log import TaskLog


# 导出所有模型
__all__ = [
    "Base",
    "Project",
    "Label",
    "DatasetVersion",
    "GenerationTask",
    "Image",
    "AnnotationTask",
    "Annotation",
    "TrainingTask",
    "Model",
    "TaskLog",
]
