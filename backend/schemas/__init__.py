"""
Pydantic Schema包
Schema Package

导入所有Schema类用于API请求/响应验证
"""

# 通用Schema
from backend.schemas.common import (
    ErrorDetail,
    HealthResponse,
    PagedResponse,
    PaginationParams,
    StatsResponse,
    SuccessResponse,
    TaskStatusResponse,
)

# 项目Schema
from backend.schemas.project import (
    LabelCreate,
    LabelResponse,
    LabelUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
)

# 图片生成Schema
from backend.schemas.generation import (
    BatchReviewRequest,
    GenerationTaskCreate,
    GenerationTaskResponse,
    ImageResponse,
    ImageReviewRequest,
    PromptTemplate,
    PromptTemplateCategory,
)

# 标注Schema
from backend.schemas.annotation import (
    AnnotationResponse,
    AnnotationTaskCreate,
    AnnotationTaskResponse,
    AnnotationVerifyRequest,
)

# 数据集Schema
from backend.schemas.dataset import (
    DatasetStatistics,
    DatasetVersionCreate,
    DatasetVersionResponse,
)

# 训练Schema
from backend.schemas.training import (
    ModelResponse,
    TrainingTaskCreate,
    TrainingTaskResponse,
)


__all__ = [
    # Common
    "PaginationParams",
    "PagedResponse",
    "SuccessResponse",
    "ErrorDetail",
    "TaskStatusResponse",
    "HealthResponse",
    "StatsResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectDetail",
    "ProjectListItem",
    "LabelCreate",
    "LabelUpdate",
    "LabelResponse",
    # Generation
    "GenerationTaskCreate",
    "GenerationTaskResponse",
    "ImageResponse",
    "ImageReviewRequest",
    "BatchReviewRequest",
    "PromptTemplate",
    "PromptTemplateCategory",
    # Annotation
    "AnnotationTaskCreate",
    "AnnotationTaskResponse",
    "AnnotationResponse",
    "AnnotationVerifyRequest",
    # Dataset
    "DatasetVersionCreate",
    "DatasetVersionResponse",
    "DatasetStatistics",
    # Training
    "TrainingTaskCreate",
    "TrainingTaskResponse",
    "ModelResponse",
]
