"""Inference monitoring and metrics collection.

This module provides monitoring, metrics, and performance tracking
for the inference service.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class InferenceMetrics:
    """Metrics tracker for inference operations."""

    def __init__(self, window_size: int = 1000):
        """Initialize metrics tracker.

        Args:
            window_size: Number of recent operations to track
        """
        self.window_size = window_size
        self._lock = threading.Lock()

        # Overall metrics
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0

        # Time tracking
        self.start_time = datetime.now()
        self.last_request_time = None

        # Recent operations (sliding window)
        self.recent_inference_times = deque(maxlen=window_size)
        self.recent_annotation_counts = deque(maxlen=window_size)

        # Per-model metrics
        self.model_metrics = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_time': 0.0,
            'annotations': 0
        })

        # Per-label metrics
        self.label_metrics = defaultdict(lambda: {
            'detections': 0,
            'avg_confidence': 0.0,
            'confidence_sum': 0.0
        })

        # Error tracking
        self.errors = deque(maxlen=100)

    def record_request(
        self,
        success: bool,
        inference_time: float,
        model_name: str,
        annotations: List[Dict[str, Any]],
        error: Optional[str] = None
    ):
        """Record an inference request.

        Args:
            success: Whether request was successful
            inference_time: Time taken for inference
            model_name: Name of model used
            annotations: List of annotations produced
            error: Error message if failed
        """
        with self._lock:
            self.total_requests += 1
            self.last_request_time = datetime.now()

            if success:
                self.total_successes += 1

                # Record timing
                self.recent_inference_times.append(inference_time)

                # Record annotations
                annotation_count = len(annotations)
                self.recent_annotation_counts.append(annotation_count)

                # Update model metrics
                model_stats = self.model_metrics[model_name]
                model_stats['requests'] += 1
                model_stats['successes'] += 1
                model_stats['total_time'] += inference_time
                model_stats['annotations'] += annotation_count

                # Update label metrics
                for ann in annotations:
                    label = ann.get('label', 'unknown')
                    confidence = ann.get('confidence', 0.0)

                    label_stats = self.label_metrics[label]
                    label_stats['detections'] += 1
                    label_stats['confidence_sum'] += confidence
                    label_stats['avg_confidence'] = (
                        label_stats['confidence_sum'] / label_stats['detections']
                    )

            else:
                self.total_failures += 1

                # Update model metrics
                model_stats = self.model_metrics[model_name]
                model_stats['requests'] += 1
                model_stats['failures'] += 1

                # Record error
                if error:
                    self.errors.append({
                        'timestamp': datetime.now().isoformat(),
                        'model': model_name,
                        'error': error
                    })

    def record_cache_hit(self):
        """Record a cache hit."""
        with self._lock:
            self.total_cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        with self._lock:
            self.total_cache_misses += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dictionary with summary metrics
        """
        with self._lock:
            # Calculate rates
            uptime = (datetime.now() - self.start_time).total_seconds()
            requests_per_second = self.total_requests / uptime if uptime > 0 else 0

            # Calculate success rate
            success_rate = (
                self.total_successes / self.total_requests
                if self.total_requests > 0 else 0
            )

            # Calculate cache hit rate
            total_cache_requests = self.total_cache_hits + self.total_cache_misses
            cache_hit_rate = (
                self.total_cache_hits / total_cache_requests
                if total_cache_requests > 0 else 0
            )

            # Calculate average inference time
            if self.recent_inference_times:
                avg_inference_time = sum(self.recent_inference_times) / len(
                    self.recent_inference_times
                )
                min_inference_time = min(self.recent_inference_times)
                max_inference_time = max(self.recent_inference_times)
            else:
                avg_inference_time = 0.0
                min_inference_time = 0.0
                max_inference_time = 0.0

            # Calculate average annotations per image
            if self.recent_annotation_counts:
                avg_annotations = sum(self.recent_annotation_counts) / len(
                    self.recent_annotation_counts
                )
            else:
                avg_annotations = 0.0

            return {
                'uptime_seconds': uptime,
                'total_requests': self.total_requests,
                'total_successes': self.total_successes,
                'total_failures': self.total_failures,
                'success_rate': success_rate,
                'requests_per_second': requests_per_second,
                'cache': {
                    'hits': self.total_cache_hits,
                    'misses': self.total_cache_misses,
                    'hit_rate': cache_hit_rate
                },
                'inference_time': {
                    'avg': avg_inference_time,
                    'min': min_inference_time,
                    'max': max_inference_time
                },
                'annotations': {
                    'avg_per_image': avg_annotations
                },
                'last_request': (
                    self.last_request_time.isoformat()
                    if self.last_request_time else None
                )
            }

    def get_model_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get per-model metrics.

        Returns:
            Dictionary of model metrics
        """
        with self._lock:
            metrics = {}

            for model_name, stats in self.model_metrics.items():
                # Calculate averages
                avg_time = (
                    stats['total_time'] / stats['successes']
                    if stats['successes'] > 0 else 0
                )

                metrics[model_name] = {
                    'requests': stats['requests'],
                    'successes': stats['successes'],
                    'failures': stats['failures'],
                    'avg_inference_time': avg_time,
                    'total_annotations': stats['annotations']
                }

            return metrics

    def get_label_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get per-label metrics.

        Returns:
            Dictionary of label metrics
        """
        with self._lock:
            return dict(self.label_metrics)

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of recent errors
        """
        with self._lock:
            return list(self.errors)[-limit:]

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.total_requests = 0
            self.total_successes = 0
            self.total_failures = 0
            self.total_cache_hits = 0
            self.total_cache_misses = 0

            self.start_time = datetime.now()
            self.last_request_time = None

            self.recent_inference_times.clear()
            self.recent_annotation_counts.clear()

            self.model_metrics.clear()
            self.label_metrics.clear()
            self.errors.clear()

            logger.info("Inference metrics reset")


class InferenceMonitor:
    """Monitor for inference service."""

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
        """Initialize monitor."""
        if hasattr(self, '_initialized'):
            return

        self.metrics = InferenceMetrics()
        self._initialized = True

        logger.info("InferenceMonitor initialized")

    def record_inference(
        self,
        success: bool,
        inference_time: float,
        model_name: str,
        annotations: List[Dict[str, Any]],
        used_cache: bool = False,
        error: Optional[str] = None
    ):
        """Record an inference operation.

        Args:
            success: Whether inference was successful
            inference_time: Time taken
            model_name: Model used
            annotations: Annotations produced
            used_cache: Whether result came from cache
            error: Error message if failed
        """
        if used_cache:
            self.metrics.record_cache_hit()
        else:
            self.metrics.record_cache_miss()

        self.metrics.record_request(
            success=success,
            inference_time=inference_time,
            model_name=model_name,
            annotations=annotations,
            error=error
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            'summary': self.metrics.get_summary(),
            'models': self.metrics.get_model_metrics(),
            'labels': self.metrics.get_label_metrics(),
            'recent_errors': self.metrics.get_recent_errors()
        }

    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics.reset()


# Global instance
_inference_monitor = None


def get_inference_monitor() -> InferenceMonitor:
    """Get global inference monitor instance."""
    global _inference_monitor
    if _inference_monitor is None:
        _inference_monitor = InferenceMonitor()
    return _inference_monitor
