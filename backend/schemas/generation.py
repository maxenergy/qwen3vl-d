"""
图片生成相关Schema
Generation Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============ Generation Task Schemas ============

class GenerationTaskCreate(BaseModel):
    """创建生成任务请求"""
    task_name: str = Field(description="任务名称")
    num_images: int = Field(gt=0, le=1000, description="生成图片数量")
    resolution: str = Field(default="640x640", pattern=r"^\d+x\d+$", description="分辨率")
    mode: str = Field(default="text_to_image", pattern=r"^(text_to_image|image_to_image)$")
    
    # 文本模式
    prompts: Optional[List[str]] = Field(default=None, description="提示词列表")
    prompt_template: Optional[str] = Field(default=None, description="提示词模板ID")
    template_params: Optional[Dict] = Field(default=None, description="模板参数")
    
    # 图片+文本模式
    reference_images: Optional[List[str]] = Field(default=None, description="参考图片路径")
    reference_prompts: Optional[List[str]] = Field(default=None, description="参考提示词")


class GenerationTaskResponse(BaseModel):
    """生成任务响应"""
    task_id: int
    task_name: str
    status: str
    num_images: int
    progress: int = Field(ge=0, le=100)
    generated_count: int
    reviewed_count: int
    approved_count: int
    elapsed_time: Optional[int] = Field(default=None, description="已用时间(秒)")
    estimated_remaining: Optional[int] = Field(default=None, description="预计剩余时间(秒)")
    created_at: datetime
    started_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ Image Schemas ============

class ImageResponse(BaseModel):
    """图片响应"""
    id: int
    filename: str
    resolution: Optional[str]
    file_size: Optional[int]
    prompt: Optional[str]
    review_status: str
    created_at: datetime
    thumbnail_url: str
    full_url: str
    
    class Config:
        from_attributes = True


class ImageReviewRequest(BaseModel):
    """图片审核请求"""
    status: str = Field(pattern=r"^(approved|rejected)$", description="审核状态")
    notes: Optional[str] = Field(default=None, description="审核备注")


class BatchReviewRequest(BaseModel):
    """批量审核请求"""
    image_ids: List[int] = Field(description="图片ID列表")
    status: str = Field(pattern=r"^(approved|rejected)$")


# ============ Template Schemas ============

class PromptTemplateVariable(BaseModel):
    """模板变量"""
    type: str = Field(description="变量类型: enum, string, number")
    options: Optional[List[str]] = Field(default=None, description="enum类型的选项")
    default: Optional[str] = None


class PromptTemplate(BaseModel):
    """提示词模板"""
    id: str
    name: str
    template: str
    variables: Dict[str, PromptTemplateVariable]


class PromptTemplateCategory(BaseModel):
    """模板分类"""
    name: str
    display_name: str
    templates: List[PromptTemplate]


# 导出
__all__ = [
    "GenerationTaskCreate",
    "GenerationTaskResponse",
    "ImageResponse",
    "ImageReviewRequest",
    "BatchReviewRequest",
    "PromptTemplate",
    "PromptTemplateCategory",
]
