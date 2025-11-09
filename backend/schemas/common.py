"""
通用Schema
Common Schemas

分页、响应等通用数据结构
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


# 泛型类型变量
T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class PagedResponse(BaseModel, Generic[T]):
    """分页响应"""
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    per_page: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    items: List[T] = Field(description="数据列表")


class SuccessResponse(BaseModel):
    """成功响应"""
    message: str = Field(description="成功消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="附加数据")


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class TaskStatusResponse(BaseModel):
    """任务状态响应(通用)"""
    task_id: int
    status: str  # pending, running, paused, completed, failed, cancelled
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(description="各服务状态")
    version: str = Field(description="版本号")


class StatsResponse(BaseModel):
    """统计信息响应"""
    projects: int
    total_images: int
    total_annotations: int
    models_trained: int
    disk_usage_gb: float
    gpu_available: bool


# 导出
__all__ = [
    "PaginationParams",
    "PagedResponse",
    "SuccessResponse",
    "ErrorDetail",
    "TaskStatusResponse",
    "HealthResponse",
    "StatsResponse",
]
