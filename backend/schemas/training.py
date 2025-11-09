"""
训练相关Schema
Training Schemas
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class TrainingTaskCreate(BaseModel):
    """创建训练任务请求"""
    task_name: str
    dataset_version_id: int
    yolo_version: str = Field(pattern=r"^yolov(8|11)$")
    model_size: str = Field(default="n", pattern=r"^(n|s|m|l|x)$")
    pretrained: bool = Field(default=True)
    epochs: int = Field(default=100, ge=1)
    batch_size: int = Field(default=16, ge=1)
    img_size: int = Field(default=640)
    learning_rate: float = Field(default=0.01, gt=0)
    patience: int = Field(default=50, ge=1)
    use_amp: bool = Field(default=True)
    device: str = Field(default="0")
    use_kfold: bool = Field(default=False)
    preset: Optional[str] = Field(default=None, pattern=r"^(quick|balanced|high_accuracy)$")


class TrainingTaskResponse(BaseModel):
    """训练任务响应"""
    task_id: int
    task_name: str
    status: str
    progress: int
    current_epoch: int
    total_epochs: int
    current_metrics: Optional[Dict] = None
    best_metrics: Optional[Dict] = None
    elapsed_time: Optional[int] = None
    estimated_remaining: Optional[int] = None
    gpu_info: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class ModelResponse(BaseModel):
    """模型响应"""
    id: int
    name: str
    model_version: Optional[str]
    yolo_version: str
    model_size: str
    model_path: str
    model_size_mb: Optional[float]
    metrics: Dict
    is_best: bool
    is_deployed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


__all__ = [
    "TrainingTaskCreate",
    "TrainingTaskResponse",
    "ModelResponse",
]
