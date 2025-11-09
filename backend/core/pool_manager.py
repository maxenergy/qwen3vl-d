"""Connection and resource pool management.

This module provides management for database connection pools,
Redis connection pools, and other resource pooling.
"""

import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
import threading

from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy import event, create_engine
import redis

from backend.core.config_loader import get_config

logger = logging.getLogger(__name__)


class PoolManager:
    """Manager for database and Redis connection pools."""

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
        """Initialize pool manager."""
        if hasattr(self, '_initialized'):
            return

        self.config = get_config()
        self.db_pool = None
        self.redis_pool = None
        self._stats = {
            'db_pool': {},
            'redis_pool': {}
        }
        self._initialized = True

        logger.info("PoolManager initialized")

    def configure_db_pool(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True
    ) -> Any:
        """Configure database connection pool.

        Args:
            database_url: Database URL
            pool_size: Size of the connection pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
            pool_pre_ping: Test connections before using

        Returns:
            SQLAlchemy engine with configured pool
        """
        try:
            # Create engine with connection pool
            engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                echo_pool=False  # Set to True for debugging
            )

            # Add event listeners for pool monitoring
            @event.listens_for(engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                """Log new connections."""
                logger.debug("New database connection established")
                self._stats['db_pool']['connections'] = (
                    self._stats['db_pool'].get('connections', 0) + 1
                )

            @event.listens_for(engine, "checkout")
            def receive_checkout(dbapi_conn, connection_record, connection_proxy):
                """Log connection checkouts."""
                self._stats['db_pool']['checkouts'] = (
                    self._stats['db_pool'].get('checkouts', 0) + 1
                )

            @event.listens_for(engine, "checkin")
            def receive_checkin(dbapi_conn, connection_record):
                """Log connection checkins."""
                self._stats['db_pool']['checkins'] = (
                    self._stats['db_pool'].get('checkins', 0) + 1
                )

            self.db_pool = engine.pool
            logger.info(
                f"Database pool configured: size={pool_size}, "
                f"max_overflow={max_overflow}"
            )

            return engine

        except Exception as e:
            logger.error(f"Failed to configure database pool: {e}")
            raise

    def configure_redis_pool(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        socket_keepalive: bool = True,
        health_check_interval: int = 30
    ) -> redis.Redis:
        """Configure Redis connection pool.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout
            socket_connect_timeout: Socket connect timeout
            socket_keepalive: Enable socket keepalive
            health_check_interval: Health check interval in seconds

        Returns:
            Redis client with connection pool
        """
        try:
            # Create connection pool
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                socket_keepalive=socket_keepalive,
                health_check_interval=health_check_interval,
                decode_responses=True
            )

            # Create Redis client
            redis_client = redis.Redis(connection_pool=pool)

            # Test connection
            redis_client.ping()

            self.redis_pool = pool
            logger.info(
                f"Redis pool configured: max_connections={max_connections}"
            )

            return redis_client

        except Exception as e:
            logger.error(f"Failed to configure Redis pool: {e}")
            raise

    def get_db_pool_stats(self) -> Dict[str, Any]:
        """Get database pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        if not self.db_pool:
            return {'error': 'Database pool not configured'}

        try:
            return {
                'size': self.db_pool.size(),
                'checked_in': self.db_pool.checkedin(),
                'checked_out': self.db_pool.checkedout(),
                'overflow': self.db_pool.overflow(),
                'total_connections': self._stats['db_pool'].get('connections', 0),
                'total_checkouts': self._stats['db_pool'].get('checkouts', 0),
                'total_checkins': self._stats['db_pool'].get('checkins', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get DB pool stats: {e}")
            return {'error': str(e)}

    def get_redis_pool_stats(self) -> Dict[str, Any]:
        """Get Redis pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        if not self.redis_pool:
            return {'error': 'Redis pool not configured'}

        try:
            return {
                'max_connections': self.redis_pool.max_connections,
                'connection_kwargs': {
                    'host': self.redis_pool.connection_kwargs.get('host'),
                    'port': self.redis_pool.connection_kwargs.get('port'),
                    'db': self.redis_pool.connection_kwargs.get('db')
                },
                'in_use_connections': len(self.redis_pool._in_use_connections),
                'available_connections': len(self.redis_pool._available_connections)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis pool stats: {e}")
            return {'error': str(e)}

    def get_all_stats(self) -> Dict[str, Any]:
        """Get all pool statistics.

        Returns:
            Dictionary with all pool statistics
        """
        return {
            'database_pool': self.get_db_pool_stats(),
            'redis_pool': self.get_redis_pool_stats()
        }

    def close_all(self):
        """Close all connection pools."""
        if self.db_pool:
            try:
                self.db_pool.dispose()
                logger.info("Database pool closed")
            except Exception as e:
                logger.error(f"Failed to close DB pool: {e}")

        if self.redis_pool:
            try:
                self.redis_pool.disconnect()
                logger.info("Redis pool closed")
            except Exception as e:
                logger.error(f"Failed to close Redis pool: {e}")


# Global instance
_pool_manager = None


def get_pool_manager() -> PoolManager:
    """Get global pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
    return _pool_manager


@contextmanager
def get_db_connection():
    """Context manager for getting database connection from pool.

    Usage:
        with get_db_connection() as conn:
            result = conn.execute("SELECT * FROM users")
    """
    from backend.core.database import engine

    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def get_redis_connection():
    """Context manager for getting Redis connection from pool.

    Usage:
        with get_redis_connection() as redis_client:
            redis_client.set("key", "value")
    """
    pool_manager = get_pool_manager()

    if not pool_manager.redis_pool:
        raise RuntimeError("Redis pool not configured")

    redis_client = redis.Redis(connection_pool=pool_manager.redis_pool)
    try:
        yield redis_client
    finally:
        # Connection is automatically returned to pool
        pass
