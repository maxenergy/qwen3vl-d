"""
训练和模型相关模型
Training and Model Models
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.core.database import Base


class TrainingTask(Base):
    """训练任务模型"""
    
    __tablename__ = "training_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    task_name = Column(String(255))
    
    # 训练配置
    yolo_version = Column(String(20), nullable=False)  # yolov8, yolov11
    model_size = Column(String(20), default="n")  # n, s, m, l, x
    pretrained_model = Column(String(255))
    
    # 超参数
    epochs = Column(Integer, default=100)
    batch_size = Column(Integer, default=16)
    img_size = Column(Integer, default=640)
    learning_rate = Column(Float, default=0.01)
    patience = Column(Integer, default=50)
    
    # 高级配置
    use_amp = Column(Boolean, default=True)  # Automatic Mixed Precision
    multi_scale = Column(Boolean, default=False)
    mosaic = Column(Float, default=1.0)
    config_yaml = Column(Text)
    
    # K-Fold配置
    use_kfold = Column(Boolean, default=False)
    kfold_splits = Column(Integer, default=5)
    current_fold = Column(Integer)
    
    # 任务状态
    status = Column(String(50), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0)
    current_epoch = Column(Integer, default=0)
    
    # 训练结果
    best_map50 = Column(Float)
    best_map50_95 = Column(Float)
    final_precision = Column(Float)
    final_recall = Column(Float)
    training_time_seconds = Column(Integer)
    
    # Checkpoint数据
    checkpoint = Column(JSONB)
    
    # 路径
    output_dir = Column(Text)
    checkpoint_path = Column(Text)
    best_model_path = Column(Text)
    tensorboard_dir = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Celery任务ID
    celery_task_id = Column(String(255))
    
    # 关系
    project = relationship("Project", back_populates="training_tasks")
    dataset_version = relationship("DatasetVersion", back_populates="training_tasks")
    models = relationship("Model", back_populates="training_task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrainingTask(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"


class Model(Base):
    """训练好的模型模型"""
    
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    training_task_id = Column(Integer, ForeignKey("training_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50))
    
    # 模型文件
    model_path = Column(Text, nullable=False, unique=True)
    model_size_bytes = Column(BigInteger)
    
    # 性能指标
    map50 = Column(Float)
    map50_95 = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    inference_time_ms = Column(Float)
    
    # 测试集评估
    test_results = Column(JSONB)
    
    # 标记
    is_best = Column(Boolean, default=False, nullable=False, index=True)
    is_deployed = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    training_task = relationship("TrainingTask", back_populates="models")
    project = relationship("Project", back_populates="models")
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.model_name}', is_best={self.is_best})>"
