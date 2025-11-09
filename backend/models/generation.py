"""
图片生成相关模型
Image Generation Models
"""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.core.database import Base


class GenerationTask(Base):
    """图片生成任务模型"""
    
    __tablename__ = "generation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id", ondelete="SET NULL"))
    
    # 任务配置
    task_name = Column(String(255))
    num_images = Column(Integer, nullable=False)
    resolution = Column(String(20), default="640x640")
    
    # 提示词配置
    prompt_template = Column(Text)
    prompts = Column(JSONB)  # 提示词列表
    reference_images = Column(JSONB)  # 参考图片路径列表
    
    # 任务状态
    status = Column(String(50), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0)
    generated_count = Column(Integer, default=0)
    reviewed_count = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    
    # Checkpoint数据(断点续传)
    checkpoint = Column(JSONB)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 错误信息
    error_message = Column(Text)
    
    # Celery任务ID
    celery_task_id = Column(String(255))
    
    # 关系
    project = relationship("Project", back_populates="generation_tasks")
    images = relationship("Image", back_populates="generation_task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GenerationTask(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"


class Image(Base):
    """生成的图片模型"""
    
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    generation_task_id = Column(Integer, ForeignKey("generation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True)
    
    # 图片信息
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False, unique=True)
    resolution = Column(String(20))
    file_size = Column(BigInteger)  # bytes
    
    # 生成参数
    prompt = Column(Text)
    reference_image = Column(Text)
    generation_params = Column(JSONB)
    
    # 人工审核
    review_status = Column(String(50), default="pending", nullable=False, index=True)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # 数据集分配
    split_type = Column(String(20), index=True)  # train, val, test
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    generation_task = relationship("GenerationTask", back_populates="images")
    dataset_version = relationship("DatasetVersion", back_populates="images")
    annotations = relationship("Annotation", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}', review_status='{self.review_status}')>"
