"""Configuration file management system."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    database: str = Field(default="qwen3vl_db", description="Database name")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")

    def get_url(self) -> str:
        """Get database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    """Redis configuration."""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=50, description="Max connections")

    def get_url(self) -> str:
        """Get Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=4, description="Number of workers")
    reload: bool = Field(default=True, description="Auto reload on changes")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    request_timeout: int = Field(default=300, description="Request timeout (seconds)")


class StorageConfig(BaseModel):
    """File storage configuration."""
    root: str = Field(default="./storage", description="Storage root directory")
    images_dir: str = Field(default="images", description="Images subdirectory")
    datasets_dir: str = Field(default="datasets", description="Datasets subdirectory")
    models_dir: str = Field(default="models", description="Models subdirectory")
    max_file_size_mb: int = Field(default=100, description="Max file size in MB")

    @field_validator('root', 'images_dir', 'datasets_dir', 'models_dir')
    @classmethod
    def ensure_path(cls, v: str) -> str:
        """Ensure path exists."""
        path = Path(v)
        if not path.is_absolute():
            path = Path.cwd() / path
        path.mkdir(parents=True, exist_ok=True)
        return str(path)


class ModelConfig(BaseModel):
    """AI model configuration."""
    qwen3vl_api_url: str = Field(
        default="http://localhost:9292/v1",
        description="Qwen3-VL API URL"
    )
    qwen3vl_model: str = Field(
        default="qwen3-vl-30b",
        description="Qwen3-VL model name"
    )
    qwen3vl_timeout: int = Field(default=60, description="Request timeout (seconds)")

    hunyuan_api_url: str = Field(
        default="http://localhost:8000",
        description="Hunyuan Image API URL"
    )
    hunyuan_api_key: Optional[str] = Field(
        default=None,
        description="Hunyuan API key"
    )
    hunyuan_timeout: int = Field(default=120, description="Request timeout (seconds)")


class TrainingConfig(BaseModel):
    """Training configuration."""
    default_epochs: int = Field(default=100, description="Default epochs")
    default_batch_size: int = Field(default=16, description="Default batch size")
    default_img_size: int = Field(default=640, description="Default image size")
    default_device: str = Field(default="cuda:0", description="Default device")
    checkpoint_interval: int = Field(default=10, description="Checkpoint save interval")
    early_stopping_patience: int = Field(default=50, description="Early stopping patience")


class CeleryConfig(BaseModel):
    """Celery configuration."""
    broker_url: Optional[str] = Field(default=None, description="Broker URL (defaults to Redis)")
    result_backend: Optional[str] = Field(default=None, description="Result backend (defaults to Redis)")
    task_time_limit: int = Field(default=3600, description="Task time limit (seconds)")
    task_soft_time_limit: int = Field(default=3000, description="Task soft time limit (seconds)")
    worker_prefetch_multiplier: int = Field(default=4, description="Worker prefetch multiplier")
    worker_max_tasks_per_child: int = Field(default=1000, description="Max tasks per worker child")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    rotation: str = Field(default="1 day", description="Log rotation interval")
    retention: str = Field(default="30 days", description="Log retention period")


class Config(BaseModel):
    """Main configuration."""
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Environment type"
    )
    debug: bool = Field(default=True, description="Debug mode")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def model_post_init(self, __context):
        """Post-initialization hook."""
        # Set Celery URLs from Redis if not provided
        if not self.celery.broker_url:
            self.celery.broker_url = self.redis.get_url()
        if not self.celery.result_backend:
            self.celery.result_backend = self.redis.get_url()


class ConfigLoader:
    """Configuration file loader."""

    DEFAULT_CONFIG_PATHS = [
        "config.yaml",
        "config.yml",
        ".qwen3vl.yaml",
        ".qwen3vl.yml",
        os.path.expanduser("~/.qwen3vl/config.yaml"),
    ]

    @classmethod
    def load_from_file(cls, file_path: str) -> Config:
        """
        Load configuration from YAML file.

        Args:
            file_path: Path to config file

        Returns:
            Config object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If config is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            data = {}

        return Config(**data)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from file or defaults.

        Args:
            config_path: Optional path to config file

        Returns:
            Config object
        """
        # If path specified, load from there
        if config_path:
            return cls.load_from_file(config_path)

        # Try default paths
        for path in cls.DEFAULT_CONFIG_PATHS:
            try:
                return cls.load_from_file(path)
            except FileNotFoundError:
                continue

        # No config file found, use defaults
        return Config()

    @classmethod
    def save(cls, config: Config, file_path: str) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Config object
            file_path: Path to save to
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = config.model_dump(exclude_none=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def merge_configs(cls, base: Config, override: Dict[str, Any]) -> Config:
        """
        Merge override config into base config.

        Args:
            base: Base configuration
            override: Override values

        Returns:
            Merged Config object
        """
        base_dict = base.model_dump()
        cls._deep_merge(base_dict, override)
        return Config(**base_dict)

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = ConfigLoader.load()
    return _config


def set_config(config: Config) -> None:
    """Set global config instance."""
    global _config
    _config = config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = ConfigLoader.load(config_path)
    return _config
