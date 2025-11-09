"""Celery tasks for inference operations.

This module provides asynchronous inference tasks using Celery
for background processing of image annotations.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from backend.worker import celery_app
from backend.services.inference_service import get_inference_service
from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="inference.infer_single")
def infer_single_task(
    self,
    image_path: str,
    labels: List[str],
    confidence_threshold: float = 0.5,
    model_name: Optional[str] = None,
    model_version: str = "default",
    task_type: str = "detection"
) -> Dict[str, Any]:
    """Asynchronous task for single image inference.

    Args:
        self: Task instance (bound)
        image_path: Path to image file
        labels: List of labels to detect
        confidence_threshold: Minimum confidence threshold
        model_name: Optional model name
        model_version: Model version
        task_type: Type of inference task

    Returns:
        Dictionary with inference results
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Loading model...', 'progress': 0}
        )

        logger.info(f"Starting inference task for: {image_path}")

        inference_service = get_inference_service()

        # Update state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Running inference...', 'progress': 50}
        )

        # Perform inference
        result = inference_service.infer_single(
            image_path=image_path,
            labels=labels,
            confidence_threshold=confidence_threshold,
            model_name=model_name,
            model_version=model_version,
            task_type=task_type
        )

        # Update state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Completed', 'progress': 100}
        )

        logger.info(f"Inference task completed: {image_path}")

        return {
            'status': 'success',
            'result': result.to_dict()
        }

    except Exception as e:
        logger.error(f"Inference task failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(bind=True, name="inference.infer_batch")
def infer_batch_task(
    self,
    image_paths: List[str],
    labels: List[str],
    confidence_threshold: float = 0.5,
    model_name: Optional[str] = None,
    model_version: str = "default",
    task_type: str = "detection"
) -> Dict[str, Any]:
    """Asynchronous task for batch inference.

    Args:
        self: Task instance (bound)
        image_paths: List of image paths
        labels: List of labels to detect
        confidence_threshold: Minimum confidence threshold
        model_name: Optional model name
        model_version: Model version
        task_type: Type of inference task

    Returns:
        Dictionary with batch inference results
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading model...',
                'progress': 0,
                'total': len(image_paths),
                'completed': 0
            }
        )

        logger.info(f"Starting batch inference task for {len(image_paths)} images")

        inference_service = get_inference_service()
        results = []
        errors = []

        # Process each image
        for i, image_path in enumerate(image_paths, 1):
            try:
                # Update progress
                progress = int((i / len(image_paths)) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Processing image {i}/{len(image_paths)}',
                        'progress': progress,
                        'total': len(image_paths),
                        'completed': i - 1
                    }
                )

                # Perform inference
                result = inference_service.infer_single(
                    image_path=image_path,
                    labels=labels,
                    confidence_threshold=confidence_threshold,
                    model_name=model_name,
                    model_version=model_version,
                    task_type=task_type
                )

                results.append(result.to_dict())

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                errors.append({
                    'image_path': image_path,
                    'error': str(e)
                })

        # Final state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Completed',
                'progress': 100,
                'total': len(image_paths),
                'completed': len(results)
            }
        )

        logger.info(
            f"Batch inference task completed: "
            f"{len(results)}/{len(image_paths)} successful"
        )

        return {
            'status': 'success',
            'results': results,
            'errors': errors,
            'total': len(image_paths),
            'successful': len(results),
            'failed': len(errors)
        }

    except Exception as e:
        logger.error(f"Batch inference task failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(bind=True, name="inference.infer_dataset")
def infer_dataset_task(
    self,
    dataset_id: int,
    project_id: int,
    confidence_threshold: float = 0.5,
    model_name: Optional[str] = None,
    save_annotations: bool = True
) -> Dict[str, Any]:
    """Asynchronous task for dataset inference.

    This task performs inference on all images in a dataset
    and optionally saves the annotations to the database.

    Args:
        self: Task instance (bound)
        dataset_id: Dataset ID
        project_id: Project ID
        confidence_threshold: Minimum confidence threshold
        model_name: Optional model name
        save_annotations: Whether to save annotations to database

    Returns:
        Dictionary with dataset inference results
    """
    try:
        from backend.core.database import SessionLocal
        from backend.models import Dataset, Project, Image, Annotation

        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Loading dataset...', 'progress': 0}
        )

        logger.info(f"Starting dataset inference task: dataset_id={dataset_id}")

        # Get dataset from database
        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Get labels from project
            labels = [label.name for label in project.labels]

            # Get images from dataset
            images = dataset.images
            if not images:
                raise ValueError(f"Dataset {dataset_id} has no images")

            logger.info(f"Processing {len(images)} images with labels: {labels}")

            # Perform batch inference
            inference_service = get_inference_service()
            image_paths = [img.file_path for img in images]

            results = []
            annotations_created = 0

            for i, (image, image_path) in enumerate(zip(images, image_paths), 1):
                try:
                    # Update progress
                    progress = int((i / len(images)) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Processing image {i}/{len(images)}',
                            'progress': progress,
                            'total': len(images),
                            'completed': i - 1
                        }
                    )

                    # Perform inference
                    result = inference_service.infer_single(
                        image_path=image_path,
                        labels=labels,
                        confidence_threshold=confidence_threshold,
                        model_name=model_name,
                        task_type="detection"
                    )

                    results.append(result.to_dict())

                    # Save annotations if requested
                    if save_annotations and result.annotations:
                        for ann_data in result.annotations:
                            # Find label
                            label = next(
                                (l for l in project.labels if l.name == ann_data['label']),
                                None
                            )

                            if label:
                                # Create annotation
                                annotation = Annotation(
                                    image_id=image.id,
                                    label_id=label.id,
                                    bbox=ann_data.get('bbox'),
                                    confidence=ann_data.get('confidence', 1.0),
                                    source='auto'
                                )
                                db.add(annotation)
                                annotations_created += 1

                        db.commit()

                except Exception as e:
                    logger.error(f"Failed to process image {image.id}: {e}")
                    continue

            # Update dataset status
            dataset.annotation_status = 'completed'
            db.commit()

            logger.info(
                f"Dataset inference completed: {len(results)} images processed, "
                f"{annotations_created} annotations created"
            )

            return {
                'status': 'success',
                'dataset_id': dataset_id,
                'total_images': len(images),
                'processed': len(results),
                'annotations_created': annotations_created,
                'results': results
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Dataset inference task failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name="inference.preload_model")
def preload_model_task(
    model_name: str = "Qwen/Qwen3-VL-2B-Instruct",
    model_version: str = "default"
) -> Dict[str, Any]:
    """Preload a model into memory.

    This task is useful for warming up models at startup.

    Args:
        model_name: Model name to preload
        model_version: Model version

    Returns:
        Dictionary with model loading status
    """
    try:
        logger.info(f"Preloading model: {model_name}:{model_version}")

        from backend.services.model_manager import get_model_manager
        model_manager = get_model_manager()

        model_info = model_manager.load_model(
            model_name=model_name,
            version=model_version
        )

        logger.info(f"Model preloaded successfully: {model_name}:{model_version}")

        return {
            'status': 'success',
            'model': model_info.get_stats()
        }

    except Exception as e:
        logger.error(f"Model preload failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
