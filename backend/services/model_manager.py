"""Model management for inference service.

This module provides model loading, caching, and lifecycle management
for the Qwen3-VL model used in inference.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import threading
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


class ModelInfo:
    """Model information and metadata."""

    def __init__(
        self,
        name: str,
        version: str,
        path: str,
        device: str = "cuda"
    ):
        self.name = name
        self.version = version
        self.path = path
        self.device = device
        self.loaded_at: Optional[datetime] = None
        self.last_used_at: Optional[datetime] = None
        self.use_count: int = 0
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        self._lock = threading.Lock()

    def mark_used(self):
        """Mark model as used."""
        with self._lock:
            self.last_used_at = datetime.now()
            self.use_count += 1

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.processor is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics."""
        return {
            "name": self.name,
            "version": self.version,
            "device": self.device,
            "loaded": self.is_loaded(),
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "use_count": self.use_count
        }


class ModelManager:
    """Manager for loading and caching models."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize model manager."""
        if hasattr(self, '_initialized'):
            return

        self.config = get_config()
        self.models: Dict[str, ModelInfo] = {}
        self._load_lock = threading.Lock()
        self._initialized = True

        logger.info("ModelManager initialized")

    def _get_device(self) -> str:
        """Get device for model inference."""
        if torch.cuda.is_available():
            device = f"cuda:{self.config.model.device_id}"
            logger.info(f"Using GPU device: {device}")
            return device
        else:
            logger.warning("CUDA not available, using CPU")
            return "cpu"

    def load_model(
        self,
        model_name: str = "Qwen/Qwen3-VL-2B-Instruct",
        model_path: Optional[str] = None,
        version: str = "default",
        force_reload: bool = False
    ) -> ModelInfo:
        """Load a model for inference.

        Args:
            model_name: Model name or identifier
            model_path: Optional custom model path
            version: Model version identifier
            force_reload: Force reload even if already loaded

        Returns:
            ModelInfo object with loaded model
        """
        model_key = f"{model_name}:{version}"

        # Check if already loaded
        if model_key in self.models and not force_reload:
            model_info = self.models[model_key]
            if model_info.is_loaded():
                logger.info(f"Model already loaded: {model_key}")
                return model_info

        # Load model with lock
        with self._load_lock:
            # Double-check after acquiring lock
            if model_key in self.models and not force_reload:
                model_info = self.models[model_key]
                if model_info.is_loaded():
                    return model_info

            logger.info(f"Loading model: {model_key}")
            start_time = time.time()

            # Determine model path
            if model_path is None:
                model_path = self.config.model.model_path or model_name

            # Get device
            device = self._get_device()

            try:
                # Load processor
                logger.info(f"Loading processor from: {model_path}")
                processor = AutoProcessor.from_pretrained(
                    model_path,
                    trust_remote_code=True
                )

                # Load model
                logger.info(f"Loading model from: {model_path}")
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.bfloat16 if device.startswith("cuda") else torch.float32,
                    device_map="auto" if device.startswith("cuda") else None,
                    trust_remote_code=True
                )

                if not device.startswith("cuda"):
                    model = model.to(device)

                # Set to eval mode
                model.eval()

                # Create model info
                model_info = ModelInfo(
                    name=model_name,
                    version=version,
                    path=str(model_path),
                    device=device
                )
                model_info.model = model
                model_info.processor = processor
                model_info.loaded_at = datetime.now()

                # Cache model
                self.models[model_key] = model_info

                load_time = time.time() - start_time
                logger.info(f"Model loaded successfully in {load_time:.2f}s: {model_key}")

                return model_info

            except Exception as e:
                logger.error(f"Failed to load model {model_key}: {e}")
                raise

    def get_model(
        self,
        model_name: str = "Qwen/Qwen3-VL-2B-Instruct",
        version: str = "default",
        auto_load: bool = True
    ) -> Optional[ModelInfo]:
        """Get a loaded model.

        Args:
            model_name: Model name
            version: Model version
            auto_load: Automatically load if not loaded

        Returns:
            ModelInfo if found/loaded, None otherwise
        """
        model_key = f"{model_name}:{version}"

        if model_key in self.models:
            model_info = self.models[model_key]
            if model_info.is_loaded():
                model_info.mark_used()
                return model_info

        if auto_load:
            return self.load_model(model_name, version=version)

        return None

    def unload_model(self, model_name: str, version: str = "default") -> bool:
        """Unload a model from memory.

        Args:
            model_name: Model name
            version: Model version

        Returns:
            True if unloaded, False if not found
        """
        model_key = f"{model_name}:{version}"

        if model_key not in self.models:
            return False

        with self._load_lock:
            model_info = self.models[model_key]

            # Clear model and processor
            if model_info.model is not None:
                del model_info.model
                model_info.model = None

            if model_info.processor is not None:
                del model_info.processor
                model_info.processor = None

            # Force garbage collection
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"Model unloaded: {model_key}")
            return True

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded models.

        Returns:
            Dictionary of model statistics
        """
        return {
            key: info.get_stats()
            for key, info in self.models.items()
        }

    def get_default_model(self) -> ModelInfo:
        """Get the default model for inference.

        Returns:
            Default model info
        """
        model_name = self.config.model.model_path or "Qwen/Qwen3-VL-2B-Instruct"
        return self.get_model(model_name, version="default", auto_load=True)


# Global instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
