"""
数据集相关Schema
Dataset Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetVersionCreate(BaseModel):
    """创建数据集版本请求"""
    version: str = Field(description="版本号, 如v1.0")
    description: Optional[str] = None
    source_task_ids: Dict[str, List[int]] = Field(description="源任务ID {'generation': [...], 'annotation': [...]}")
    split_ratio: Dict[str, float] = Field(default={"train": 0.8, "val": 0.1, "test": 0.1})
    random_seed: int = Field(default=42)
    export_formats: List[str] = Field(default=["yolo"])
    augmentation: Optional[Dict] = None
    kfold: Optional[Dict] = None


class DatasetVersionResponse(BaseModel):
    """数据集版本响应"""
    id: int
    version: str
    description: Optional[str]
    status: str
    total_images: int
    total_annotations: int
    train_count: int
    val_count: int
    test_count: int
    export_formats: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetStatistics(BaseModel):
    """数据集统计"""
    total_images: int
    total_annotations: int
    label_distribution: Dict[str, int]
    split_distribution: Dict[str, Dict[str, int]]


__all__ = [
    "DatasetVersionCreate",
    "DatasetVersionResponse",
    "DatasetStatistics",
]
