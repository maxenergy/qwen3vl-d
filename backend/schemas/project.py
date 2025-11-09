"""
项目相关Schema
Project Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============ Label Schemas ============

class LabelBase(BaseModel):
    """标签基础Schema"""
    name: str = Field(min_length=1, max_length=100, description="标签名称")
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$", description="HEX颜色代码")
    description: Optional[str] = Field(default=None, description="标签描述")
    
    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v and not v.startswith("#"):
            return f"#{v}"
        return v


class LabelCreate(LabelBase):
    """创建标签请求"""
    pass


class LabelUpdate(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LabelResponse(LabelBase):
    """标签响应"""
    id: int
    project_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Project Schemas ============

class ProjectBase(BaseModel):
    """项目基础Schema"""
    name: str = Field(min_length=3, max_length=255, description="项目名称")
    description: Optional[str] = Field(default=None, description="项目描述")


class ProjectCreate(ProjectBase):
    """创建项目请求"""
    labels: Optional[List[LabelCreate]] = Field(default=None, description="初始标签列表")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern=r"^(active|archived)$")
    settings: Optional[Dict] = None


class ProjectResponse(ProjectBase):
    """项目响应"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    labels: List[LabelResponse] = []
    
    class Config:
        from_attributes = True


class ProjectDetail(ProjectResponse):
    """项目详情响应"""
    statistics: Optional[Dict] = Field(default=None, description="统计信息")
    versions: Optional[List] = Field(default=None, description="数据集版本列表")


class ProjectListItem(BaseModel):
    """项目列表项"""
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    label_count: int = 0
    image_count: int = 0
    annotation_count: int = 0
    
    class Config:
        from_attributes = True


# 导出
__all__ = [
    "LabelBase",
    "LabelCreate",
    "LabelUpdate",
    "LabelResponse",
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectDetail",
    "ProjectListItem",
]
