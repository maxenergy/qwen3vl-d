"""Integration tests for inference API."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from backend.services.inference_service import InferenceResult


class TestInferenceAPI:
    """Test inference API endpoints."""

    @pytest.fixture
    def mock_inference_result(self):
        """Create mock inference result."""
        return InferenceResult(
            image_path="/test/image.jpg",
            annotations=[
                {
                    "label": "car",
                    "confidence": 0.95,
                    "bbox": [10, 20, 100, 150],
                    "type": "detection"
                }
            ],
            inference_time=1.5,
            model_name="test-model",
            model_version="1.0",
            confidence_threshold=0.5
        )

    @patch('backend.api.routes.inference.get_inference_service')
    def test_infer_image(self, mock_get_service, client: TestClient, mock_inference_result):
        """Test single image inference endpoint."""
        # Setup mock
        mock_service = Mock()
        mock_service.infer_single.return_value = mock_inference_result
        mock_get_service.return_value = mock_service

        # Make request
        request_data = {
            "image_path": "/test/image.jpg",
            "labels": ["car", "person"],
            "confidence_threshold": 0.5
        }

        response = client.post("/api/v1/inference/infer", json=request_data)

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["image_path"] == "/test/image.jpg"
        assert len(data["annotations"]) == 1
        assert data["annotations"][0]["label"] == "car"
        assert data["inference_time"] == 1.5

    @patch('backend.api.routes.inference.get_inference_service')
    def test_infer_image_not_found(self, mock_get_service, client: TestClient):
        """Test inference with non-existent image."""
        # Setup mock to raise FileNotFoundError
        mock_service = Mock()
        mock_service.infer_single.side_effect = FileNotFoundError("Image not found")
        mock_get_service.return_value = mock_service

        # Make request
        request_data = {
            "image_path": "/nonexistent/image.jpg",
            "labels": ["car"]
        }

        response = client.post("/api/v1/inference/infer", json=request_data)

        # Check response
        assert response.status_code == 404

    @patch('backend.api.routes.inference.get_inference_service')
    def test_infer_batch(self, mock_get_service, client: TestClient, mock_inference_result):
        """Test batch inference endpoint."""
        # Setup mock
        mock_service = Mock()
        mock_service.infer_batch.return_value = [
            mock_inference_result,
            mock_inference_result
        ]
        mock_get_service.return_value = mock_service

        # Make request
        request_data = {
            "image_paths": ["/test/image1.jpg", "/test/image2.jpg"],
            "labels": ["car", "person"],
            "confidence_threshold": 0.5
        }

        response = client.post("/api/v1/inference/infer/batch", json=request_data)

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["total_images"] == 2
        assert data["successful"] == 2
        assert data["failed"] == 0
        assert len(data["results"]) == 2

    @patch('backend.api.routes.inference.get_model_manager')
    def test_list_models(self, mock_get_manager, client: TestClient):
        """Test list models endpoint."""
        # Setup mock
        mock_manager = Mock()
        mock_manager.list_models.return_value = {
            "test-model:default": {
                "name": "test-model",
                "version": "default",
                "loaded": True,
                "device": "cpu"
            }
        }
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.get("/api/v1/inference/models")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert "test-model:default" in data["models"]

    @patch('backend.api.routes.inference.get_model_manager')
    def test_load_model(self, mock_get_manager, client: TestClient):
        """Test load model endpoint."""
        # Setup mock
        mock_model_info = Mock()
        mock_model_info.get_stats.return_value = {
            "name": "test-model",
            "version": "1.0",
            "loaded": True
        }

        mock_manager = Mock()
        mock_manager.load_model.return_value = mock_model_info
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.post(
            "/api/v1/inference/models/load?model_name=test-model&model_version=1.0"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "loaded"
        assert "model" in data

    @patch('backend.api.routes.inference.get_model_manager')
    def test_unload_model(self, mock_get_manager, client: TestClient):
        """Test unload model endpoint."""
        # Setup mock
        mock_manager = Mock()
        mock_manager.unload_model.return_value = True
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.delete(
            "/api/v1/inference/models/test-model?model_version=1.0"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "unloaded"

    @patch('backend.api.routes.inference.get_model_manager')
    def test_unload_model_not_found(self, mock_get_manager, client: TestClient):
        """Test unloading non-existent model."""
        # Setup mock
        mock_manager = Mock()
        mock_manager.unload_model.return_value = False
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.delete(
            "/api/v1/inference/models/nonexistent?model_version=1.0"
        )

        # Check response
        assert response.status_code == 404

    @patch('backend.api.routes.inference.get_inference_service')
    def test_get_inference_stats(self, mock_get_service, client: TestClient):
        """Test get inference stats endpoint."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_stats.return_value = {
            "total_inferences": 100,
            "total_images": 100,
            "total_inference_time": 150.0,
            "avg_inference_time": 1.5,
            "errors": 5
        }
        mock_get_service.return_value = mock_service

        # Make request
        response = client.get("/api/v1/inference/stats")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["total_inferences"] == 100
        assert data["avg_inference_time"] == 1.5

    @patch('backend.api.routes.inference.get_inference_service')
    def test_reset_inference_stats(self, mock_get_service, client: TestClient):
        """Test reset inference stats endpoint."""
        # Setup mock
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Make request
        response = client.post("/api/v1/inference/stats/reset")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "reset"
        mock_service.reset_stats.assert_called_once()

    @patch('backend.api.routes.inference.get_inference_monitor')
    def test_get_metrics(self, mock_get_monitor, client: TestClient):
        """Test get metrics endpoint."""
        # Setup mock
        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {
            "summary": {
                "uptime_seconds": 3600,
                "total_requests": 100,
                "success_rate": 0.95
            },
            "models": {},
            "labels": {}
        }
        mock_get_monitor.return_value = mock_monitor

        # Make request
        response = client.get("/api/v1/inference/metrics")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert data["summary"]["total_requests"] == 100

    @patch('backend.api.routes.inference.get_inference_monitor')
    def test_reset_metrics(self, mock_get_monitor, client: TestClient):
        """Test reset metrics endpoint."""
        # Setup mock
        mock_monitor = Mock()
        mock_get_monitor.return_value = mock_monitor

        # Make request
        response = client.post("/api/v1/inference/metrics/reset")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "reset"
        mock_monitor.reset_metrics.assert_called_once()

    @patch('backend.api.routes.inference.get_model_manager')
    @patch('backend.api.routes.inference.get_inference_monitor')
    def test_health_check(self, mock_get_monitor, mock_get_manager, client: TestClient):
        """Test inference health check endpoint."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.list_models.return_value = {
            "model1": {"loaded": True},
            "model2": {"loaded": False}
        }
        mock_get_manager.return_value = mock_manager

        mock_monitor = Mock()
        mock_monitor.get_metrics.return_value = {
            "summary": {
                "success_rate": 0.95,
                "requests_per_second": 10.0,
                "last_request": "2024-01-01T00:00:00"
            }
        }
        mock_get_monitor.return_value = mock_monitor

        # Make request
        with patch('backend.api.routes.inference.get_inference_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.healthcheck.return_value = True
            mock_get_cache.return_value = mock_cache

            response = client.get("/api/v1/inference/health")

        # Check response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["models_loaded"] == 1
        assert data["cache_available"] is True
        assert data["success_rate"] == 0.95


class TestInferenceValidation:
    """Test inference API validation."""

    def test_infer_missing_required_fields(self, client: TestClient):
        """Test inference with missing required fields."""
        # Missing 'labels' field
        request_data = {
            "image_path": "/test/image.jpg"
        }

        response = client.post("/api/v1/inference/infer", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_infer_invalid_confidence(self, client: TestClient):
        """Test inference with invalid confidence threshold."""
        # Confidence out of range
        request_data = {
            "image_path": "/test/image.jpg",
            "labels": ["car"],
            "confidence_threshold": 1.5  # Invalid
        }

        response = client.post("/api/v1/inference/infer", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_batch_infer_empty_list(self, client: TestClient):
        """Test batch inference with empty image list."""
        request_data = {
            "image_paths": [],  # Empty
            "labels": ["car"]
        }

        # This should be handled by validation or business logic
        response = client.post("/api/v1/inference/infer/batch", json=request_data)

        # Either validation error or success with 0 results
        assert response.status_code in [200, 422]
