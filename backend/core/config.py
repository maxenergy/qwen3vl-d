"""
配置管理模块
Configuration Management

使用Pydantic Settings管理所有配置
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 应用配置
    app_name: str = Field(default="Auto Annotation Tool", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/auto_annotation",
        description="数据库连接URL"
    )
    db_echo: bool = Field(default=False, description="是否打印SQL")
    
    # Redis配置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # Celery配置
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery Broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery Result Backend"
    )
    
    # Qwen3-VL API配置
    qwen3vl_api_url: str = Field(
        default="http://192.168.8.147:9292/v1",
        description="Qwen3-VL API地址"
    )
    qwen3vl_model: str = Field(
        default="qwen3-vl-30b",
        description="Qwen3-VL模型名称"
    )
    qwen3vl_api_key: Optional[str] = Field(
        default=None,
        description="Qwen3-VL API密钥"
    )
    
    # Hunyuan配置
    hunyuan_model_path: str = Field(
        default="models/hunyuan",
        description="Hunyuan模型路径"
    )
    hunyuan_api_url: Optional[str] = Field(
        default=None,
        description="Hunyuan API地址(如果使用API)"
    )
    hunyuan_api_key: Optional[str] = Field(
        default=None,
        description="Hunyuan API密钥"
    )
    
    # 文件存储
    data_dir: str = Field(default="data", description="数据目录")
    models_dir: str = Field(default="models", description="模型目录")
    upload_max_size_mb: int = Field(default=100, description="上传文件最大大小(MB)")
    
    # 安全配置
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="密钥"
    )
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Token过期时间(分钟)"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/app.log", description="日志文件")
    
    # YOLO训练配置
    default_device: str = Field(default="0", description="默认GPU设备")
    default_batch_size: int = Field(default=16, description="默认批次大小")
    default_epochs: int = Field(default=100, description="默认训练轮数")
    
    # TensorBoard配置
    tensorboard_port: int = Field(default=6006, description="TensorBoard端口")
    
    # Gradio配置
    gradio_port: int = Field(default=7860, description="Gradio端口")
    gradio_share: bool = Field(default=False, description="Gradio是否分享")
    
    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:7860"],
        description="允许的CORS来源"
    )
    
    @field_validator("data_dir", "models_dir")
    @classmethod
    def resolve_path(cls, v: str) -> Path:
        """将相对路径转换为绝对路径"""
        path = Path(v)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @field_validator("log_file")
    @classmethod
    def resolve_log_path(cls, v: str) -> Path:
        """确保日志目录存在"""
        log_path = Path(v)
        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path
    
    @property
    def database_url_async(self) -> str:
        """异步数据库URL"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def projects_dir(self) -> Path:
        """项目数据目录"""
        return Path(self.data_dir) / "projects"
    
    @property
    def pretrained_yolo_dir(self) -> Path:
        """预训练YOLO模型目录"""
        return Path(self.models_dir) / "pretrained_yolo"


# 创建全局配置实例
settings = Settings()


# 导出常用路径
DATA_DIR = settings.data_dir
MODELS_DIR = settings.models_dir
PROJECTS_DIR = settings.projects_dir
PRETRAINED_YOLO_DIR = settings.pretrained_yolo_dir
PROJECT_ROOT = PROJECT_ROOT


if __name__ == "__main__":
    # 测试配置
    print("=" * 60)
    print("配置信息:")
    print("=" * 60)
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"环境: {settings.environment}")
    print(f"数据库: {settings.database_url}")
    print(f"Redis: {settings.redis_url}")
    print(f"数据目录: {settings.data_dir}")
    print(f"模型目录: {settings.models_dir}")
    print(f"Qwen3-VL API: {settings.qwen3vl_api_url}")
    print("=" * 60)
