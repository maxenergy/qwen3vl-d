"""
标注相关Schema
Annotation Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnnotationTaskCreate(BaseModel):
    """创建标注任务请求"""
    task_name: str
    dataset_version: Optional[str] = None
    label_names: List[str] = Field(description="要标注的类别名称列表")
    image_ids: Optional[List[int]] = Field(default=None, description="指定图片ID,或使用image_source")
    image_source: Optional[str] = Field(default=None, description="图片来源: all_approved等")
    generation_task_id: Optional[int] = None
    confidence_threshold: float = Field(default=0.3, ge=0.1, le=0.9)
    max_detections_per_image: int = Field(default=100, ge=1)
    api_endpoint: Optional[str] = Field(default=None)
    model_name: Optional[str] = Field(default=None)


class AnnotationTaskResponse(BaseModel):
    """标注任务响应"""
    task_id: int
    task_name: str
    status: str
    progress: int
    total_images: int
    annotated_images: int
    total_annotations: int = 0
    avg_detections_per_image: Optional[float] = None
    avg_time_per_image: Optional[float] = None
    elapsed_time: Optional[int] = None
    estimated_remaining: Optional[int] = None
    
    class Config:
        from_attributes = True


class AnnotationResponse(BaseModel):
    """标注响应"""
    id: int
    label: str
    label_id: int
    bbox: List[float] = Field(description="[x1, y1, x2, y2] 0-1000")
    confidence: Optional[float]
    normalized_coords: Dict[str, float] = Field(description="YOLO格式归一化坐标")
    is_verified: bool
    
    class Config:
        from_attributes = True


class AnnotationVerifyRequest(BaseModel):
    """标注校验请求"""
    is_correct: bool
    correction_bbox: Optional[List[float]] = Field(default=None, description="修正的bbox")
    notes: Optional[str] = None


__all__ = [
    "AnnotationTaskCreate",
    "AnnotationTaskResponse",
    "AnnotationResponse",
    "AnnotationVerifyRequest",
]
