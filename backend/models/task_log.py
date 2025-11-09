"""
任务日志模型
Task Log Model
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from backend.core.database import Base


class TaskLog(Base):
    """任务日志模型"""
    
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # generation, annotation, training
    task_id = Column(Integer, nullable=False, index=True)
    level = Column(String(20), default="INFO", nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<TaskLog(id={self.id}, task_type='{self.task_type}', task_id={self.task_id}, level='{self.level}')>"
