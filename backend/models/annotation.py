"""
标注相关模型
Annotation Models
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from backend.core.database import Base


class AnnotationTask(Base):
    """标注任务模型"""
    
    __tablename__ = "annotation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True)
    
    task_name = Column(String(255))
    
    # 标注配置
    label_ids = Column(ARRAY(Integer))  # 要标注的标签ID列表
    image_ids = Column(ARRAY(Integer))  # 要标注的图片ID列表
    confidence_threshold = Column(Float, default=0.3)
    max_detections_per_image = Column(Integer, default=100)
    
    # 任务状态
    status = Column(String(50), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0)
    total_images = Column(Integer, default=0)
    annotated_images = Column(Integer, default=0)
    
    # Qwen3-VL API配置
    api_endpoint = Column(String(255))
    model_name = Column(String(100))
    
    # Checkpoint数据
    checkpoint = Column(JSONB)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Celery任务ID
    celery_task_id = Column(String(255))
    
    # 关系
    project = relationship("Project", back_populates="annotation_tasks")
    dataset_version = relationship("DatasetVersion", back_populates="annotation_tasks")
    annotations = relationship("Annotation", back_populates="annotation_task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnnotationTask(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"


class Annotation(Base):
    """标注结果模型"""
    
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    annotation_task_id = Column(Integer, ForeignKey("annotation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    label_id = Column(Integer, ForeignKey("labels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 标注数据 (Qwen3-VL原始坐标, 0-1000)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    confidence = Column(Float)
    
    # 归一化坐标 (YOLO格式: center_x, center_y, width, height, 0-1)
    normalized_x = Column(Float)
    normalized_y = Column(Float)
    normalized_w = Column(Float)
    normalized_h = Column(Float)
    
    # 人工校验
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    is_correct = Column(Boolean, index=True)
    correction_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    annotation_task = relationship("AnnotationTask", back_populates="annotations")
    image = relationship("Image", back_populates="annotations")
    label = relationship("Label", back_populates="annotations")
    
    # 约束
    __table_args__ = (
        CheckConstraint(
            "bbox_x1 >= 0 AND bbox_y1 >= 0 AND bbox_x2 <= 1000 AND bbox_y2 <= 1000 AND bbox_x1 < bbox_x2 AND bbox_y1 < bbox_y2",
            name="bbox_check"
        ),
    )
    
    def __repr__(self):
        return f"<Annotation(id={self.id}, image_id={self.image_id}, label_id={self.label_id})>"
