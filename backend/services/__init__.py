"""
服务层模块

提供业务逻辑和外部服务集成
"""

from backend.services.hunyuan_generator import HunyuanImageGenerator
from backend.services.prompt_template import (
    PromptTemplate,
    PromptTemplateManager,
    template_manager,
)

__all__ = [
    "HunyuanImageGenerator",
    "PromptTemplate",
    "PromptTemplateManager",
    "template_manager",
]
