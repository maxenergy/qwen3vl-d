"""Unit tests for inference service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.services.inference_service import InferenceService, InferenceResult
from backend.services.model_manager import ModelInfo
from backend.services.inference_cache import InferenceCache


class TestInferenceService:
    """Test InferenceService class."""

    @pytest.fixture
    def inference_service(self):
        """Create inference service instance."""
        with patch('backend.services.inference_service.get_model_manager'):
            with patch('backend.services.inference_service.get_inference_cache'):
                service = InferenceService()
                return service

    @pytest.fixture
    def mock_model_info(self):
        """Create mock model info."""
        model_info = Mock(spec=ModelInfo)
        model_info.name = "test-model"
        model_info.version = "1.0"
        model_info.device = "cpu"
        model_info.model = Mock()
        model_info.processor = Mock()
        return model_info

    def test_init(self, inference_service):
        """Test inference service initialization."""
        assert inference_service is not None
        assert isinstance(inference_service.stats, dict)
        assert inference_service.stats["total_inferences"] == 0
        assert "cache_hits" in inference_service.stats
        assert "cache_misses" in inference_service.stats

    def test_build_prompt_detection(self, inference_service):
        """Test prompt building for detection task."""
        labels = ["car", "person"]
        prompt = inference_service._build_prompt(labels, task_type="detection")

        assert "car" in prompt
        assert "person" in prompt
        assert "Detect" in prompt
        assert "bounding box" in prompt

    def test_build_prompt_segmentation(self, inference_service):
        """Test prompt building for segmentation task."""
        labels = ["car", "person"]
        prompt = inference_service._build_prompt(labels, task_type="segmentation")

        assert "car" in prompt
        assert "person" in prompt
        assert "Segment" in prompt

    def test_build_prompt_invalid_task(self, inference_service):
        """Test prompt building with invalid task type."""
        labels = ["car"]

        with pytest.raises(ValueError, match="Unknown task type"):
            inference_service._build_prompt(labels, task_type="invalid")

    def test_parse_model_output_valid_json(self, inference_service):
        """Test parsing valid model output."""
        output = '''
        {
            "detections": [
                {"label": "car", "confidence": 0.95, "bbox": [10, 20, 100, 150]},
                {"label": "person", "confidence": 0.85, "bbox": [50, 60, 80, 120]}
            ]
        }
        '''

        labels = ["car", "person"]
        annotations = inference_service._parse_model_output(
            output, labels, confidence_threshold=0.5
        )

        assert len(annotations) == 2
        assert annotations[0]["label"] == "car"
        assert annotations[0]["confidence"] == 0.95
        assert annotations[1]["label"] == "person"

    def test_parse_model_output_below_threshold(self, inference_service):
        """Test parsing with confidence threshold filtering."""
        output = '''
        [
            {"label": "car", "confidence": 0.95, "bbox": [10, 20, 100, 150]},
            {"label": "person", "confidence": 0.3, "bbox": [50, 60, 80, 120]}
        ]
        '''

        labels = ["car", "person"]
        annotations = inference_service._parse_model_output(
            output, labels, confidence_threshold=0.5
        )

        # Only one annotation should pass threshold
        assert len(annotations) == 1
        assert annotations[0]["label"] == "car"

    def test_parse_model_output_invalid_json(self, inference_service):
        """Test parsing invalid JSON output."""
        output = "This is not valid JSON"

        labels = ["car"]
        annotations = inference_service._parse_model_output(
            output, labels, confidence_threshold=0.5
        )

        # Should return empty list for invalid output
        assert annotations == []

    def test_get_stats(self, inference_service):
        """Test getting inference statistics."""
        # Set some stats
        inference_service.stats["total_inferences"] = 10
        inference_service.stats["total_inference_time"] = 50.0

        stats = inference_service.get_stats()

        assert stats["total_inferences"] == 10
        assert stats["avg_inference_time"] == 5.0

    def test_get_stats_no_inferences(self, inference_service):
        """Test getting stats with no inferences."""
        stats = inference_service.get_stats()

        assert stats["total_inferences"] == 0
        assert stats["avg_inference_time"] == 0.0

    def test_reset_stats(self, inference_service):
        """Test resetting statistics."""
        # Set some stats
        inference_service.stats["total_inferences"] = 10
        inference_service.stats["errors"] = 5

        # Reset
        inference_service.reset_stats()

        # Check all reset to zero
        assert inference_service.stats["total_inferences"] == 0
        assert inference_service.stats["errors"] == 0


class TestInferenceResult:
    """Test InferenceResult class."""

    def test_init(self):
        """Test InferenceResult initialization."""
        annotations = [
            {"label": "car", "confidence": 0.95, "bbox": [10, 20, 100, 150]}
        ]

        result = InferenceResult(
            image_path="/path/to/image.jpg",
            annotations=annotations,
            inference_time=1.5,
            model_name="test-model",
            model_version="1.0",
            confidence_threshold=0.5
        )

        assert result.image_path == "/path/to/image.jpg"
        assert len(result.annotations) == 1
        assert result.inference_time == 1.5
        assert result.model_name == "test-model"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        annotations = [
            {"label": "car", "confidence": 0.95, "bbox": [10, 20, 100, 150]}
        ]

        result = InferenceResult(
            image_path="/path/to/image.jpg",
            annotations=annotations,
            inference_time=1.5,
            model_name="test-model",
            model_version="1.0",
            confidence_threshold=0.5
        )

        result_dict = result.to_dict()

        assert result_dict["image_path"] == "/path/to/image.jpg"
        assert len(result_dict["annotations"]) == 1
        assert result_dict["annotation_count"] == 1
        assert result_dict["inference_time"] == 1.5
        assert "timestamp" in result_dict


class TestInferenceCache:
    """Test InferenceCache class."""

    @pytest.fixture
    def cache(self):
        """Create cache instance with disabled Redis."""
        with patch('backend.services.inference_cache.get_config') as mock_config:
            mock_config.return_value.redis.enabled = False
            cache = InferenceCache()
            return cache

    def test_init_disabled(self, cache):
        """Test cache initialization when disabled."""
        assert cache.enabled is False
        assert cache.redis_client is None

    def test_generate_cache_key(self, cache):
        """Test cache key generation."""
        key1 = cache._generate_cache_key(
            image_path="/path/image.jpg",
            labels=["car", "person"],
            confidence_threshold=0.5,
            model_name="test-model",
            model_version="1.0",
            task_type="detection"
        )

        key2 = cache._generate_cache_key(
            image_path="/path/image.jpg",
            labels=["person", "car"],  # Different order
            confidence_threshold=0.5,
            model_name="test-model",
            model_version="1.0",
            task_type="detection"
        )

        # Keys should be same despite different label order
        assert key1 == key2
        assert key1.startswith("inference:result:")

    def test_generate_cache_key_different_params(self, cache):
        """Test cache key generation with different parameters."""
        key1 = cache._generate_cache_key(
            image_path="/path/image.jpg",
            labels=["car"],
            confidence_threshold=0.5,
            model_name="test-model",
            model_version="1.0",
            task_type="detection"
        )

        key2 = cache._generate_cache_key(
            image_path="/path/image.jpg",
            labels=["car"],
            confidence_threshold=0.7,  # Different threshold
            model_name="test-model",
            model_version="1.0",
            task_type="detection"
        )

        # Keys should be different
        assert key1 != key2

    def test_get_disabled(self, cache):
        """Test cache get when disabled."""
        result = cache.get(
            image_path="/path/image.jpg",
            labels=["car"],
            confidence_threshold=0.5,
            model_name="test-model",
            model_version="1.0"
        )

        assert result is None

    def test_set_disabled(self, cache):
        """Test cache set when disabled."""
        success = cache.set(
            image_path="/path/image.jpg",
            labels=["car"],
            confidence_threshold=0.5,
            model_name="test-model",
            model_version="1.0",
            task_type="detection",
            result={"test": "data"}
        )

        assert success is False

    def test_get_stats_disabled(self, cache):
        """Test getting stats when disabled."""
        stats = cache.get_stats()

        assert stats["enabled"] is False
        assert stats["status"] == "disabled"

    def test_healthcheck_disabled(self, cache):
        """Test healthcheck when disabled."""
        assert cache.healthcheck() is False
