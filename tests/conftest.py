"""Pytest configuration and fixtures."""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from backend.core.database import Base, get_db
from backend.api.main import app


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def sample_image(temp_dir: Path) -> Path:
    """Create a sample image file for testing."""
    from PIL import Image
    import numpy as np

    # Create a simple test image
    img_array = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)

    img_path = temp_dir / "test_image.jpg"
    img.save(img_path)

    return img_path


@pytest.fixture(scope="function")
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit tests",
        "labels": [
            {"name": "car", "color": "#FF0000"},
            {"name": "person", "color": "#00FF00"}
        ]
    }


@pytest.fixture(scope="function")
def sample_generation_task_data():
    """Sample generation task data for testing."""
    return {
        "name": "Test Generation",
        "prompt": "A photo of a car on a highway",
        "batch_size": 10,
        "resolution": "640x640",
        "mode": "text_to_image"
    }


@pytest.fixture(scope="function")
def sample_annotation_task_data():
    """Sample annotation task data for testing."""
    return {
        "name": "Test Annotation",
        "image_ids": [1, 2, 3],
        "label_ids": [1, 2],
        "confidence_threshold": 0.5
    }


@pytest.fixture(scope="function")
def sample_dataset_data():
    """Sample dataset data for testing."""
    return {
        "version": "v1.0.0",
        "description": "Test dataset",
        "split_config": {
            "train_ratio": 0.7,
            "val_ratio": 0.2,
            "test_ratio": 0.1
        },
        "export_formats": ["yolo", "coco"]
    }


@pytest.fixture(scope="function")
def sample_training_task_data():
    """Sample training task data for testing."""
    return {
        "name": "Test Training",
        "dataset_id": 1,
        "yolo_version": "yolov8n",
        "hyperparameters": {
            "epochs": 10,
            "batch": 8,
            "imgsz": 640,
            "lr0": 0.01
        }
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'ERROR'
    os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'true'

    yield

    # Cleanup
    for key in ['TESTING', 'LOG_LEVEL', 'CELERY_TASK_ALWAYS_EAGER']:
        os.environ.pop(key, None)
