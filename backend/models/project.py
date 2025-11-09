"""
项目和标签数据模型
Project and Label Models
"""

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Project(Base):
    """项目模型"""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)
    settings = Column(JSONB)
    
    # 关系
    labels = relationship("Label", back_populates="project", cascade="all, delete-orphan")
    dataset_versions = relationship("DatasetVersion", back_populates="project", cascade="all, delete-orphan")
    generation_tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")
    annotation_tasks = relationship("AnnotationTask", back_populates="project", cascade="all, delete-orphan")
    training_tasks = relationship("TrainingTask", back_populates="project", cascade="all, delete-orphan")
    models = relationship("Model", back_populates="project", cascade="all, delete-orphan")
    
    # 约束
    __table_args__ = (
        CheckConstraint("char_length(name) >= 3", name="project_name_check"),
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class Label(Base):
    """标签模型"""
    
    __tablename__ = "labels"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7))  # HEX color code
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="labels")
    annotations = relationship("Annotation", back_populates="label", cascade="all, delete-orphan")
    
    # 约束
    __table_args__ = (
        CheckConstraint("project_id IS NOT NULL", name="label_project_check"),
    )
    
    def __repr__(self):
        return f"<Label(id={self.id}, name='{self.name}', project_id={self.project_id})>"
