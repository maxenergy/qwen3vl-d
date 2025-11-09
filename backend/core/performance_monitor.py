"""Performance monitoring and profiling tools.

This module provides performance monitoring, request timing,
and system resource tracking.
"""

import logging
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque
import threading

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """System performance and resource monitor."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, window_size: int = 1000):
        """Initialize performance monitor.

        Args:
            window_size: Number of requests to track
        """
        if hasattr(self, '_initialized'):
            return

        self.window_size = window_size
        self.request_times = deque(maxlen=window_size)
        self.endpoint_stats = {}
        self.start_time = datetime.now()
        self._lock_stats = threading.Lock()
        self._initialized = True

        logger.info("PerformanceMonitor initialized")

    def record_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """Record API request metrics.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            duration: Request duration in seconds
            status_code: HTTP status code
            error: Error message if any
        """
        with self._lock_stats:
            # Record in sliding window
            self.request_times.append({
                'timestamp': datetime.now(),
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code,
                'error': error
            })

            # Update endpoint stats
            key = f"{method} {endpoint}"
            if key not in self.endpoint_stats:
                self.endpoint_stats[key] = {
                    'count': 0,
                    'total_time': 0.0,
                    'errors': 0,
                    'min_time': float('inf'),
                    'max_time': 0.0
                }

            stats = self.endpoint_stats[key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)

            if error or status_code >= 400:
                stats['errors'] += 1

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics.

        Returns:
            Dictionary with system metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except Exception:
                network_stats = {}

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': network_stats
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    def get_request_metrics(self) -> Dict[str, Any]:
        """Get API request metrics.

        Returns:
            Dictionary with request metrics
        """
        with self._lock_stats:
            if not self.request_times:
                return {
                    'total_requests': 0,
                    'avg_response_time': 0.0,
                    'min_response_time': 0.0,
                    'max_response_time': 0.0,
                    'error_rate': 0.0
                }

            durations = [r['duration'] for r in self.request_times]
            errors = sum(1 for r in self.request_times if r['error'] or r['status_code'] >= 400)

            return {
                'total_requests': len(self.request_times),
                'avg_response_time': sum(durations) / len(durations),
                'min_response_time': min(durations),
                'max_response_time': max(durations),
                'error_rate': errors / len(self.request_times) if self.request_times else 0.0,
                'errors': errors
            }

    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-endpoint statistics.

        Returns:
            Dictionary of endpoint statistics
        """
        with self._lock_stats:
            result = {}

            for endpoint, stats in self.endpoint_stats.items():
                result[endpoint] = {
                    'count': stats['count'],
                    'avg_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0.0,
                    'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0.0,
                    'max_time': stats['max_time'],
                    'errors': stats['errors'],
                    'error_rate': stats['errors'] / stats['count'] if stats['count'] > 0 else 0.0
                }

            return result

    def get_slowest_endpoints(self, limit: int = 10) -> list:
        """Get slowest endpoints.

        Args:
            limit: Number of endpoints to return

        Returns:
            List of slowest endpoints
        """
        with self._lock_stats:
            endpoint_times = []

            for endpoint, stats in self.endpoint_stats.items():
                avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0.0
                endpoint_times.append({
                    'endpoint': endpoint,
                    'avg_time': avg_time,
                    'count': stats['count']
                })

            return sorted(endpoint_times, key=lambda x: x['avg_time'], reverse=True)[:limit]

    def get_summary(self) -> Dict[str, Any]:
        """Get complete performance summary.

        Returns:
            Dictionary with complete metrics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'uptime_seconds': uptime,
            'system': self.get_system_metrics(),
            'requests': self.get_request_metrics(),
            'slowest_endpoints': self.get_slowest_endpoints(5)
        }

    def reset(self):
        """Reset all metrics."""
        with self._lock_stats:
            self.request_times.clear()
            self.endpoint_stats.clear()
            self.start_time = datetime.now()
            logger.info("Performance metrics reset")


# Global instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
