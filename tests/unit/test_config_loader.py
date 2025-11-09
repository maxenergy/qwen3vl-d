"""Unit tests for configuration loader."""

import pytest
import tempfile
import yaml
from pathlib import Path

from backend.core.config_loader import (
    ConfigLoader, Config, DatabaseConfig, RedisConfig,
    APIConfig, Environment
)


class TestDatabaseConfig:
    """Test DatabaseConfig model."""

    def test_get_url(self):
        """Test database URL generation."""
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )

        expected = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert db_config.get_url() == expected

    def test_defaults(self):
        """Test default values."""
        db_config = DatabaseConfig()

        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.pool_size == 20
        assert db_config.max_overflow == 10


class TestRedisConfig:
    """Test RedisConfig model."""

    def test_get_url_no_password(self):
        """Test Redis URL without password."""
        redis_config = RedisConfig(host="localhost", port=6379, db=0)

        expected = "redis://localhost:6379/0"
        assert redis_config.get_url() == expected

    def test_get_url_with_password(self):
        """Test Redis URL with password."""
        redis_config = RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            password="secret"
        )

        expected = "redis://:secret@localhost:6379/0"
        assert redis_config.get_url() == expected


class TestConfig:
    """Test main Config model."""

    def test_defaults(self):
        """Test default configuration."""
        config = Config()

        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is True
        assert config.database.host == "localhost"
        assert config.redis.host == "localhost"
        assert config.api.port == 8000

    def test_custom_values(self):
        """Test custom configuration values."""
        config = Config(
            environment=Environment.PRODUCTION,
            debug=False,
            database={"host": "db.example.com", "port": 5433}
        )

        assert config.environment == Environment.PRODUCTION
        assert config.debug is False
        assert config.database.host == "db.example.com"
        assert config.database.port == 5433

    def test_celery_urls_from_redis(self):
        """Test Celery URLs default to Redis URLs."""
        config = Config()

        redis_url = config.redis.get_url()
        assert config.celery.broker_url == redis_url
        assert config.celery.result_backend == redis_url


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_from_file(self):
        """Test loading config from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "environment": "production",
                "debug": False,
                "database": {
                    "host": "prod-db.example.com",
                    "port": 5432
                }
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConfigLoader.load_from_file(temp_path)

            assert config.environment == Environment.PRODUCTION
            assert config.debug is False
            assert config.database.host == "prod-db.example.com"
        finally:
            Path(temp_path).unlink()

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_file("nonexistent.yaml")

    def test_load_defaults(self):
        """Test loading with no config file (uses defaults)."""
        config = ConfigLoader.load(config_path=None)

        assert isinstance(config, Config)
        assert config.environment == Environment.DEVELOPMENT

    def test_save(self):
        """Test saving config to file."""
        config = Config(
            environment=Environment.TEST,
            debug=True,
            database={"host": "test-db", "port": 5433}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            ConfigLoader.save(config, temp_path)

            # Load it back
            loaded_config = ConfigLoader.load_from_file(temp_path)

            assert loaded_config.environment == Environment.TEST
            assert loaded_config.database.host == "test-db"
            assert loaded_config.database.port == 5433
        finally:
            Path(temp_path).unlink()

    def test_merge_configs(self):
        """Test merging configurations."""
        base = Config(
            database={"host": "localhost", "port": 5432},
            redis={"host": "localhost"}
        )

        override = {
            "database": {"host": "remote-db"},
            "api": {"port": 9000}
        }

        merged = ConfigLoader.merge_configs(base, override)

        # Overridden values
        assert merged.database.host == "remote-db"
        assert merged.api.port == 9000

        # Preserved values
        assert merged.database.port == 5432
        assert merged.redis.host == "localhost"

    def test_deep_merge(self):
        """Test deep merge functionality."""
        base = {
            "database": {"host": "localhost", "port": 5432},
            "api": {"host": "0.0.0.0", "port": 8000}
        }

        override = {
            "database": {"host": "remote"},
            "api": {"port": 9000}
        }

        ConfigLoader._deep_merge(base, override)

        assert base["database"]["host"] == "remote"
        assert base["database"]["port"] == 5432  # Preserved
        assert base["api"]["host"] == "0.0.0.0"  # Preserved
        assert base["api"]["port"] == 9000  # Overridden


class TestEnvironmentEnum:
    """Test Environment enum."""

    def test_values(self):
        """Test environment values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TEST.value == "test"

    def test_from_string(self):
        """Test creating environment from string."""
        env = Environment("production")
        assert env == Environment.PRODUCTION


class TestAPIConfig:
    """Test APIConfig model."""

    def test_defaults(self):
        """Test default API configuration."""
        api_config = APIConfig()

        assert api_config.host == "0.0.0.0"
        assert api_config.port == 8000
        assert api_config.workers == 4
        assert api_config.reload is True
        assert "http://localhost:3000" in api_config.cors_origins

    def test_custom_cors(self):
        """Test custom CORS origins."""
        api_config = APIConfig(
            cors_origins=["https://example.com", "https://app.example.com"]
        )

        assert len(api_config.cors_origins) == 2
        assert "https://example.com" in api_config.cors_origins
