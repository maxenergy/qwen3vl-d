"""API response caching middleware.

This middleware provides automatic caching of API responses using Redis
to improve performance and reduce database load.
"""

import logging
import hashlib
import json
from typing import Optional, List, Callable
from datetime import timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import redis

from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


class APICacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses."""

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        default_ttl: int = 300,
        cache_get_only: bool = True,
        exclude_paths: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None
    ):
        """Initialize cache middleware.

        Args:
            app: FastAPI application
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (default: 300 = 5 minutes)
            cache_get_only: Only cache GET requests
            exclude_paths: List of paths to exclude from caching
            include_patterns: List of path patterns to include
        """
        super().__init__(app)

        self.config = get_config()
        self.default_ttl = default_ttl
        self.cache_get_only = cache_get_only
        self.exclude_paths = exclude_paths or [
            "/api/v1/health",
            "/api/v1/inference",  # Don't cache inference results
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        self.include_patterns = include_patterns or []

        # Initialize Redis
        if redis_client:
            self.redis_client = redis_client
            self.enabled = True
        elif self.config.redis.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.redis.host,
                    port=self.config.redis.port,
                    db=self.config.redis.db,
                    password=self.config.redis.password if self.config.redis.password else None,
                    decode_responses=False,  # We handle encoding
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                self.enabled = True
                logger.info("API cache middleware enabled with Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
                self.redis_client = None
                self.enabled = False
        else:
            self.redis_client = None
            self.enabled = False
            logger.info("API cache middleware disabled in configuration")

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }

    def _should_cache(self, request: Request) -> bool:
        """Check if request should be cached.

        Args:
            request: Request object

        Returns:
            True if should cache, False otherwise
        """
        # Check if caching is enabled
        if not self.enabled:
            return False

        # Check HTTP method
        if self.cache_get_only and request.method != "GET":
            return False

        # Check excluded paths
        path = request.url.path
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return False

        # Check include patterns (if specified)
        if self.include_patterns:
            for pattern in self.include_patterns:
                if pattern in path:
                    return True
            return False

        # Default: cache all other GET requests
        return True

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request.

        Args:
            request: Request object

        Returns:
            Cache key string
        """
        # Include path, query params, and relevant headers
        key_parts = [
            request.method,
            request.url.path,
            str(request.url.query)
        ]

        # Include authorization header if present (for user-specific caching)
        if "authorization" in request.headers:
            key_parts.append(request.headers["authorization"])

        # Generate hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"api:cache:{key_hash}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and cache response.

        Args:
            request: Request object
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        # Check if should cache
        if not self._should_cache(request):
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        try:
            # Try to get from cache
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                # Cache hit
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {request.url.path}")

                # Deserialize cached response
                cached_response = json.loads(cached_data)

                # Create response with cached data
                response = Response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"],
                    media_type=cached_response.get("media_type", "application/json")
                )

                # Add cache header
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key

                return response

            # Cache miss - call next handler
            self.stats["misses"] += 1
            logger.debug(f"Cache miss: {request.url.path}")

            response = await call_next(request)

            # Cache response if successful
            if response.status_code == 200:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Serialize response
                cached_response = {
                    "content": body.decode("utf-8"),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }

                # Store in cache
                self.redis_client.setex(
                    cache_key,
                    self.default_ttl,
                    json.dumps(cached_response)
                )

                # Create new response with cached body
                new_response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

                # Add cache header
                new_response.headers["X-Cache"] = "MISS"
                new_response.headers["X-Cache-Key"] = cache_key

                return new_response

            return response

        except Exception as e:
            # Log error but don't break the request
            self.stats["errors"] += 1
            logger.error(f"Cache error: {e}")
            return await call_next(request)

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "hit_rate": hit_rate,
            "total_requests": total
        }

    def clear_cache(self, pattern: str = "api:cache:*") -> int:
        """Clear cached responses.

        Args:
            pattern: Redis key pattern to clear

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cached responses")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def invalidate_path(self, path_pattern: str):
        """Invalidate cache for specific path pattern.

        Args:
            path_pattern: Path pattern to invalidate
        """
        # This is a simplified implementation
        # In production, you'd want more sophisticated cache invalidation
        self.clear_cache()


# Decorator for custom cache control
def cache_response(ttl: int = 300):
    """Decorator to customize cache TTL for specific endpoints.

    Args:
        ttl: Time to live in seconds

    Usage:
        @app.get("/api/v1/projects")
        @cache_response(ttl=600)  # Cache for 10 minutes
        async def get_projects():
            ...
    """
    def decorator(func):
        func._cache_ttl = ttl
        return func
    return decorator


# Dependency for disabling cache on specific endpoints
def no_cache():
    """Dependency to disable caching for specific endpoints.

    Usage:
        @app.get("/api/v1/projects", dependencies=[Depends(no_cache)])
        async def get_projects():
            ...
    """
    pass
