"""
数据集版本模型
Dataset Version Model
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from backend.core.database import Base


class DatasetVersion(Base):
    """数据集版本模型"""
    
    __tablename__ = "dataset_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 统计信息
    total_images = Column(Integer, default=0)
    total_annotations = Column(Integer, default=0)
    train_count = Column(Integer, default=0)
    val_count = Column(Integer, default=0)
    test_count = Column(Integer, default=0)
    
    # 数据集配置
    split_ratio = Column(JSONB)  # {"train": 0.8, "val": 0.1, "test": 0.1}
    augmentation_config = Column(JSONB)
    export_formats = Column(ARRAY(String))  # ["yolo", "coco"]
    
    status = Column(String(50), default="building", nullable=False, index=True)
    
    # 关系
    project = relationship("Project", back_populates="dataset_versions")
    images = relationship("Image", back_populates="dataset_version")
    annotation_tasks = relationship("AnnotationTask", back_populates="dataset_version")
    training_tasks = relationship("TrainingTask", back_populates="dataset_version")
    
    def __repr__(self):
        return f"<DatasetVersion(id={self.id}, version='{self.version}', project_id={self.project_id})>"
