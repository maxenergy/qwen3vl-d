"""Inference API endpoints."""

import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

from backend.services.inference_service import get_inference_service
from backend.services.model_manager import get_model_manager
from backend.services.inference_monitor import get_inference_monitor
from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inference", tags=["inference"])


# Pydantic models
class InferenceRequest(BaseModel):
    """Request for single image inference."""

    image_path: str = Field(..., description="Path to image file")
    labels: List[str] = Field(..., description="List of labels to detect")
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional model name (uses default if not provided)"
    )
    model_version: str = Field(
        default="default",
        description="Model version to use"
    )
    task_type: str = Field(
        default="detection",
        description="Type of task (detection, segmentation)"
    )


class BatchInferenceRequest(BaseModel):
    """Request for batch inference."""

    image_paths: List[str] = Field(..., description="List of image paths")
    labels: List[str] = Field(..., description="List of labels to detect")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model_name: Optional[str] = None
    model_version: str = "default"
    task_type: str = "detection"


class InferenceResponse(BaseModel):
    """Response from inference."""

    image_path: str
    annotations: List[dict]
    inference_time: float
    model_name: str
    model_version: str
    confidence_threshold: float
    timestamp: str
    annotation_count: int


class BatchInferenceResponse(BaseModel):
    """Response from batch inference."""

    results: List[InferenceResponse]
    total_images: int
    successful: int
    failed: int
    total_time: float


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    version: str
    device: str
    loaded: bool
    loaded_at: Optional[str]
    last_used_at: Optional[str]
    use_count: int


class InferenceStats(BaseModel):
    """Inference statistics."""

    total_inferences: int
    total_images: int
    total_inference_time: float
    avg_inference_time: float
    errors: int


@router.post("/infer", response_model=InferenceResponse)
async def infer_image(request: InferenceRequest):
    """Perform inference on a single image.

    This endpoint performs object detection or segmentation on a single image
    using the specified labels and confidence threshold.

    Args:
        request: Inference request with image path and parameters

    Returns:
        InferenceResponse with annotations and metadata

    Raises:
        HTTPException: If inference fails
    """
    try:
        logger.info(f"Inference request for: {request.image_path}")

        inference_service = get_inference_service()

        result = inference_service.infer_single(
            image_path=request.image_path,
            labels=request.labels,
            confidence_threshold=request.confidence_threshold,
            model_name=request.model_name,
            model_version=request.model_version,
            task_type=request.task_type
        )

        return InferenceResponse(**result.to_dict())

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@router.post("/infer/batch", response_model=BatchInferenceResponse)
async def infer_batch(request: BatchInferenceRequest):
    """Perform inference on multiple images.

    This endpoint performs batch inference on multiple images using the
    same labels and confidence threshold.

    Args:
        request: Batch inference request

    Returns:
        BatchInferenceResponse with results for all images

    Raises:
        HTTPException: If batch inference fails
    """
    try:
        logger.info(f"Batch inference request for {len(request.image_paths)} images")

        inference_service = get_inference_service()

        import time
        start_time = time.time()

        results = inference_service.infer_batch(
            image_paths=request.image_paths,
            labels=request.labels,
            confidence_threshold=request.confidence_threshold,
            model_name=request.model_name,
            model_version=request.model_version,
            task_type=request.task_type
        )

        total_time = time.time() - start_time

        return BatchInferenceResponse(
            results=[InferenceResponse(**r.to_dict()) for r in results],
            total_images=len(request.image_paths),
            successful=len(results),
            failed=len(request.image_paths) - len(results),
            total_time=total_time
        )

    except Exception as e:
        logger.error(f"Batch inference failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch inference failed: {str(e)}"
        )


@router.post("/infer/upload", response_model=InferenceResponse)
async def infer_uploaded_image(
    file: UploadFile = File(...),
    labels: str = Form(...),
    confidence_threshold: float = Form(0.5),
    model_name: Optional[str] = Form(None),
    task_type: str = Form("detection")
):
    """Perform inference on an uploaded image.

    This endpoint accepts an image file upload and performs inference on it.

    Args:
        file: Uploaded image file
        labels: Comma-separated list of labels
        confidence_threshold: Minimum confidence threshold
        model_name: Optional model name
        task_type: Type of task

    Returns:
        InferenceResponse with annotations

    Raises:
        HTTPException: If inference fails
    """
    try:
        # Parse labels
        label_list = [l.strip() for l in labels.split(",")]

        # Save uploaded file temporarily
        config = get_config()
        upload_dir = Path(config.storage.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        import uuid
        file_id = uuid.uuid4().hex
        file_path = upload_dir / f"{file_id}_{file.filename}"

        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Uploaded file saved to: {file_path}")

        # Perform inference
        inference_service = get_inference_service()

        result = inference_service.infer_single(
            image_path=str(file_path),
            labels=label_list,
            confidence_threshold=confidence_threshold,
            model_name=model_name,
            task_type=task_type
        )

        # Clean up temporary file
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

        return InferenceResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Upload inference failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload inference failed: {str(e)}"
        )


@router.get("/models", response_model=dict)
async def list_models():
    """List all loaded models.

    Returns:
        Dictionary of loaded models with their statistics
    """
    try:
        model_manager = get_model_manager()
        models = model_manager.list_models()
        return {"models": models}

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/models/load")
async def load_model(
    model_name: str,
    model_version: str = "default",
    force_reload: bool = False
):
    """Load a model into memory.

    Args:
        model_name: Name of model to load
        model_version: Model version
        force_reload: Force reload even if already loaded

    Returns:
        Model information

    Raises:
        HTTPException: If model loading fails
    """
    try:
        logger.info(f"Loading model: {model_name}:{model_version}")

        model_manager = get_model_manager()
        model_info = model_manager.load_model(
            model_name=model_name,
            version=model_version,
            force_reload=force_reload
        )

        return {"status": "loaded", "model": model_info.get_stats()}

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )


@router.delete("/models/{model_name}")
async def unload_model(model_name: str, model_version: str = "default"):
    """Unload a model from memory.

    Args:
        model_name: Name of model to unload
        model_version: Model version

    Returns:
        Status message

    Raises:
        HTTPException: If model unloading fails
    """
    try:
        logger.info(f"Unloading model: {model_name}:{model_version}")

        model_manager = get_model_manager()
        success = model_manager.unload_model(model_name, model_version)

        if success:
            return {"status": "unloaded", "model": f"{model_name}:{model_version}"}
        else:
            raise HTTPException(status_code=404, detail="Model not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload model: {str(e)}"
        )


@router.get("/stats", response_model=InferenceStats)
async def get_inference_stats():
    """Get inference statistics.

    Returns:
        InferenceStats with current statistics
    """
    try:
        inference_service = get_inference_service()
        stats = inference_service.get_stats()
        return InferenceStats(**stats)

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/stats/reset")
async def reset_inference_stats():
    """Reset inference statistics.

    Returns:
        Status message
    """
    try:
        inference_service = get_inference_service()
        inference_service.reset_stats()
        return {"status": "reset", "message": "Inference statistics reset"}

    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset stats: {str(e)}"
        )


@router.get("/metrics")
async def get_inference_metrics():
    """Get detailed inference metrics.

    Returns comprehensive metrics including:
    - Summary statistics
    - Per-model performance
    - Per-label detection rates
    - Recent errors

    Returns:
        Dictionary with detailed metrics
    """
    try:
        monitor = get_inference_monitor()
        metrics = monitor.get_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.post("/metrics/reset")
async def reset_inference_metrics():
    """Reset inference metrics.

    Returns:
        Status message
    """
    try:
        monitor = get_inference_monitor()
        monitor.reset_metrics()
        return {"status": "reset", "message": "Inference metrics reset"}

    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset metrics: {str(e)}"
        )


@router.get("/health")
async def inference_health_check():
    """Check inference service health.

    Checks:
    - Model manager status
    - Cache connectivity
    - Recent error rate

    Returns:
        Health status dictionary
    """
    try:
        # Check model manager
        model_manager = get_model_manager()
        models = model_manager.list_models()
        models_loaded = len([m for m in models.values() if m.get('loaded', False)])

        # Check cache
        from backend.services.inference_cache import get_inference_cache
        cache = get_inference_cache()
        cache_healthy = cache.healthcheck()

        # Check metrics
        monitor = get_inference_monitor()
        metrics = monitor.get_metrics()
        summary = metrics.get('summary', {})

        # Calculate health status
        error_rate = 1 - summary.get('success_rate', 1.0)
        health_status = "healthy"

        if error_rate > 0.5:
            health_status = "unhealthy"
        elif error_rate > 0.2:
            health_status = "degraded"

        return {
            "status": health_status,
            "models_loaded": models_loaded,
            "cache_available": cache_healthy,
            "success_rate": summary.get('success_rate', 0.0),
            "requests_per_second": summary.get('requests_per_second', 0.0),
            "last_request": summary.get('last_request')
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
