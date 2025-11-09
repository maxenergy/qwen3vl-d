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
from backend.services.qwen3vl_detector import (
    BoundingBox,
    DetectionResult,
    Qwen3VLClient,
    get_qwen3vl_client,
)
from backend.services.dataset_converter import (
    YOLODatasetConverter,
    COCODatasetConverter,
    DatasetSplitter,
    DataAugmentationConfig,
)
from backend.services.yolo_trainer import YOLOTrainer

__all__ = [
    "HunyuanImageGenerator",
    "PromptTemplate",
    "PromptTemplateManager",
    "template_manager",
    "BoundingBox",
    "DetectionResult",
    "Qwen3VLClient",
    "get_qwen3vl_client",
    "YOLODatasetConverter",
    "COCODatasetConverter",
    "DatasetSplitter",
    "DataAugmentationConfig",
    "YOLOTrainer",
]
