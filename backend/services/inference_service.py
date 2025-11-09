"""Inference service for image annotation.

This module provides the core inference functionality for automatic
image annotation using the Qwen3-VL model.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from PIL import Image
import torch

from backend.services.model_manager import get_model_manager, ModelInfo
from backend.services.inference_cache import get_inference_cache
from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


class InferenceResult:
    """Result of an inference operation."""

    def __init__(
        self,
        image_path: str,
        annotations: List[Dict[str, Any]],
        inference_time: float,
        model_name: str,
        model_version: str,
        confidence_threshold: float
    ):
        self.image_path = image_path
        self.annotations = annotations
        self.inference_time = inference_time
        self.model_name = model_name
        self.model_version = model_version
        self.confidence_threshold = confidence_threshold
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "image_path": self.image_path,
            "annotations": self.annotations,
            "inference_time": self.inference_time,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "confidence_threshold": self.confidence_threshold,
            "timestamp": self.timestamp.isoformat(),
            "annotation_count": len(self.annotations)
        }


class InferenceService:
    """Service for performing inference on images."""

    def __init__(self):
        """Initialize inference service."""
        self.config = get_config()
        self.model_manager = get_model_manager()
        self.cache = get_inference_cache()
        self.stats = {
            "total_inferences": 0,
            "total_images": 0,
            "total_inference_time": 0.0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        logger.info("InferenceService initialized")

    def _prepare_image(self, image_path: Union[str, Path]) -> Image.Image:
        """Prepare image for inference.

        Args:
            image_path: Path to image file

        Returns:
            PIL Image object
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            image = Image.open(image_path)
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise

    def _build_prompt(
        self,
        labels: List[str],
        task_type: str = "detection"
    ) -> str:
        """Build prompt for the model.

        Args:
            labels: List of label names to detect
            task_type: Type of task (detection, segmentation, etc.)

        Returns:
            Formatted prompt string
        """
        if task_type == "detection":
            labels_str = ", ".join(labels)
            prompt = (
                f"Detect and locate the following objects in this image: {labels_str}. "
                f"For each object, provide: 1) the label name, "
                f"2) bounding box coordinates (x_min, y_min, x_max, y_max) in pixels, "
                f"3) confidence score (0-1). "
                f"Return results in JSON format."
            )
        elif task_type == "segmentation":
            labels_str = ", ".join(labels)
            prompt = (
                f"Segment the following objects in this image: {labels_str}. "
                f"For each object, provide: 1) the label name, "
                f"2) segmentation mask, "
                f"3) confidence score (0-1). "
                f"Return results in JSON format."
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        return prompt

    def _parse_model_output(
        self,
        output: str,
        labels: List[str],
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Parse model output into structured annotations.

        Args:
            output: Raw model output string
            labels: Expected label names
            confidence_threshold: Minimum confidence threshold

        Returns:
            List of annotation dictionaries
        """
        annotations = []

        try:
            # This is a simplified parser - in practice, you would need
            # more robust parsing based on the actual model output format
            import json
            import re

            # Try to extract JSON from output
            json_match = re.search(r'\{.*\}|\[.*\]', output, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())

                # Handle different output formats
                if isinstance(parsed, list):
                    results = parsed
                elif isinstance(parsed, dict):
                    results = parsed.get("detections", [parsed])
                else:
                    results = []

                for item in results:
                    confidence = float(item.get("confidence", 0.0))

                    # Filter by confidence threshold
                    if confidence < confidence_threshold:
                        continue

                    annotation = {
                        "label": item.get("label", "unknown"),
                        "confidence": confidence,
                        "bbox": item.get("bbox", [0, 0, 0, 0]),
                        "type": "detection"
                    }
                    annotations.append(annotation)

            logger.info(f"Parsed {len(annotations)} annotations from model output")

        except Exception as e:
            logger.warning(f"Failed to parse model output: {e}")
            # Return empty list if parsing fails
            logger.debug(f"Raw output: {output[:500]}")

        return annotations

    @torch.no_grad()
    def infer_single(
        self,
        image_path: Union[str, Path],
        labels: List[str],
        confidence_threshold: float = 0.5,
        model_name: Optional[str] = None,
        model_version: str = "default",
        task_type: str = "detection",
        use_cache: bool = True
    ) -> InferenceResult:
        """Perform inference on a single image.

        Args:
            image_path: Path to image file
            labels: List of labels to detect
            confidence_threshold: Minimum confidence threshold (0-1)
            model_name: Optional model name (uses default if None)
            model_version: Model version to use
            task_type: Type of inference task
            use_cache: Whether to use cached results

        Returns:
            InferenceResult object
        """
        start_time = time.time()

        try:
            # Get model info for cache key
            if model_name is None:
                model_name = self.config.model.model_path or "Qwen/Qwen3-VL-2B-Instruct"

            # Check cache first
            if use_cache:
                cached_result = self.cache.get(
                    image_path=str(image_path),
                    labels=labels,
                    confidence_threshold=confidence_threshold,
                    model_name=model_name,
                    model_version=model_version,
                    task_type=task_type
                )

                if cached_result:
                    logger.info(f"Using cached result for: {image_path}")
                    self.stats["cache_hits"] += 1

                    # Create result from cache
                    result = InferenceResult(
                        image_path=cached_result["image_path"],
                        annotations=cached_result["annotations"],
                        inference_time=cached_result["inference_time"],
                        model_name=cached_result["model_name"],
                        model_version=cached_result["model_version"],
                        confidence_threshold=cached_result["confidence_threshold"]
                    )
                    return result

            self.stats["cache_misses"] += 1

            # Get model
            if model_name:
                model_info = self.model_manager.get_model(
                    model_name, version=model_version
                )
            else:
                model_info = self.model_manager.get_default_model()

            # Prepare image
            image = self._prepare_image(image_path)

            # Build prompt
            prompt = self._build_prompt(labels, task_type)

            # Prepare inputs
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            # Process with model
            text = model_info.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            image_inputs, video_inputs = model_info.processor.process_vision_info(
                messages
            )

            inputs = model_info.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )

            # Move to device
            inputs = inputs.to(model_info.device)

            # Generate
            generated_ids = model_info.model.generate(
                **inputs,
                max_new_tokens=self.config.model.max_new_tokens
            )

            # Trim and decode
            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = model_info.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]

            # Parse output
            annotations = self._parse_model_output(
                output_text,
                labels,
                confidence_threshold
            )

            # Update stats
            inference_time = time.time() - start_time
            self.stats["total_inferences"] += 1
            self.stats["total_images"] += 1
            self.stats["total_inference_time"] += inference_time

            logger.info(
                f"Inference completed in {inference_time:.2f}s: "
                f"{len(annotations)} annotations found"
            )

            # Create result
            result = InferenceResult(
                image_path=str(image_path),
                annotations=annotations,
                inference_time=inference_time,
                model_name=model_info.name,
                model_version=model_info.version,
                confidence_threshold=confidence_threshold
            )

            # Cache result if enabled
            if use_cache:
                self.cache.set(
                    image_path=str(image_path),
                    labels=labels,
                    confidence_threshold=confidence_threshold,
                    model_name=model_info.name,
                    model_version=model_info.version,
                    task_type=task_type,
                    result=result.to_dict()
                )

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Inference failed for {image_path}: {e}")
            raise

    def infer_batch(
        self,
        image_paths: List[Union[str, Path]],
        labels: List[str],
        confidence_threshold: float = 0.5,
        model_name: Optional[str] = None,
        model_version: str = "default",
        task_type: str = "detection"
    ) -> List[InferenceResult]:
        """Perform inference on multiple images.

        Args:
            image_paths: List of image paths
            labels: List of labels to detect
            confidence_threshold: Minimum confidence threshold
            model_name: Optional model name
            model_version: Model version
            task_type: Type of inference task

        Returns:
            List of InferenceResult objects
        """
        results = []

        logger.info(f"Starting batch inference on {len(image_paths)} images")
        batch_start = time.time()

        for i, image_path in enumerate(image_paths, 1):
            try:
                result = self.infer_single(
                    image_path=image_path,
                    labels=labels,
                    confidence_threshold=confidence_threshold,
                    model_name=model_name,
                    model_version=model_version,
                    task_type=task_type
                )
                results.append(result)
                logger.info(f"Completed {i}/{len(image_paths)}")

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                # Continue with other images
                continue

        batch_time = time.time() - batch_start
        logger.info(
            f"Batch inference completed in {batch_time:.2f}s: "
            f"{len(results)}/{len(image_paths)} successful"
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()

        if stats["total_inferences"] > 0:
            stats["avg_inference_time"] = (
                stats["total_inference_time"] / stats["total_inferences"]
            )
        else:
            stats["avg_inference_time"] = 0.0

        return stats

    def reset_stats(self):
        """Reset inference statistics."""
        self.stats = {
            "total_inferences": 0,
            "total_images": 0,
            "total_inference_time": 0.0,
            "errors": 0
        }
        logger.info("Inference statistics reset")


# Global instance
_inference_service = None


def get_inference_service() -> InferenceService:
    """Get global inference service instance."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service
