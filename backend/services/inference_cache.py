"""Inference result caching service.

This module provides caching functionality for inference results
using Redis to improve performance and reduce redundant computations.
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import timedelta

import redis
from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


class InferenceCache:
    """Cache for inference results using Redis."""

    def __init__(self):
        """Initialize inference cache."""
        self.config = get_config()
        self.enabled = self.config.redis.enabled

        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.redis.host,
                    port=self.config.redis.port,
                    db=self.config.redis.db,
                    password=self.config.redis.password if self.config.redis.password else None,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Inference cache initialized with Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
                self.enabled = False
                self.redis_client = None
        else:
            logger.info("Inference cache disabled in configuration")
            self.redis_client = None

    def _generate_cache_key(
        self,
        image_path: str,
        labels: List[str],
        confidence_threshold: float,
        model_name: str,
        model_version: str,
        task_type: str
    ) -> str:
        """Generate a unique cache key for inference parameters.

        Args:
            image_path: Path to image file
            labels: List of labels
            confidence_threshold: Confidence threshold
            model_name: Model name
            model_version: Model version
            task_type: Type of task

        Returns:
            Cache key string
        """
        # Create a deterministic string from parameters
        key_data = {
            'image_path': image_path,
            'labels': sorted(labels),  # Sort for consistency
            'confidence_threshold': confidence_threshold,
            'model_name': model_name,
            'model_version': model_version,
            'task_type': task_type
        }

        key_string = json.dumps(key_data, sort_keys=True)

        # Generate hash
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"inference:result:{key_hash}"

    def get(
        self,
        image_path: str,
        labels: List[str],
        confidence_threshold: float,
        model_name: str,
        model_version: str,
        task_type: str = "detection"
    ) -> Optional[Dict[str, Any]]:
        """Get cached inference result.

        Args:
            image_path: Path to image file
            labels: List of labels
            confidence_threshold: Confidence threshold
            model_name: Model name
            model_version: Model version
            task_type: Type of task

        Returns:
            Cached result dictionary or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(
                image_path,
                labels,
                confidence_threshold,
                model_name,
                model_version,
                task_type
            )

            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                logger.debug(f"Cache hit for: {image_path}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for: {image_path}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        image_path: str,
        labels: List[str],
        confidence_threshold: float,
        model_name: str,
        model_version: str,
        task_type: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache inference result.

        Args:
            image_path: Path to image file
            labels: List of labels
            confidence_threshold: Confidence threshold
            model_name: Model name
            model_version: Model version
            task_type: Type of task
            result: Result dictionary to cache
            ttl: Time to live in seconds (default: 3600)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(
                image_path,
                labels,
                confidence_threshold,
                model_name,
                model_version,
                task_type
            )

            # Use default TTL if not specified
            if ttl is None:
                ttl = 3600  # 1 hour

            # Serialize and cache
            cached_data = json.dumps(result)
            self.redis_client.setex(cache_key, ttl, cached_data)

            logger.debug(f"Cached result for: {image_path}")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(
        self,
        image_path: str,
        labels: List[str],
        confidence_threshold: float,
        model_name: str,
        model_version: str,
        task_type: str = "detection"
    ) -> bool:
        """Delete cached inference result.

        Args:
            image_path: Path to image file
            labels: List of labels
            confidence_threshold: Confidence threshold
            model_name: Model name
            model_version: Model version
            task_type: Type of task

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(
                image_path,
                labels,
                confidence_threshold,
                model_name,
                model_version,
                task_type
            )

            deleted = self.redis_client.delete(cache_key)
            logger.debug(f"Deleted cache for: {image_path}")
            return bool(deleted)

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all inference caches.

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Find all inference cache keys
            keys = self.redis_client.keys("inference:result:*")

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} inference cache entries")
                return True
            else:
                logger.info("No inference cache entries to clear")
                return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {
                'enabled': False,
                'status': 'disabled'
            }

        try:
            # Get number of cached items
            keys = self.redis_client.keys("inference:result:*")
            cached_items = len(keys)

            # Get Redis info
            info = self.redis_client.info("stats")

            return {
                'enabled': True,
                'status': 'connected',
                'cached_items': cached_items,
                'redis_hits': info.get('keyspace_hits', 0),
                'redis_misses': info.get('keyspace_misses', 0),
                'redis_keys': info.get('total_keys', 0)
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'enabled': True,
                'status': 'error',
                'error': str(e)
            }

    def healthcheck(self) -> bool:
        """Check if cache is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache healthcheck failed: {e}")
            return False


# Global instance
_inference_cache = None


def get_inference_cache() -> InferenceCache:
    """Get global inference cache instance."""
    global _inference_cache
    if _inference_cache is None:
        _inference_cache = InferenceCache()
    return _inference_cache
