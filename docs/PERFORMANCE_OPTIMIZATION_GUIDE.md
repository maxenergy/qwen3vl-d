# Performance Optimization Guide

Complete guide for optimizing the AI Auto-Annotation Tool's performance.

## Overview

This guide covers performance optimization strategies including caching, database optimization, connection pooling, and monitoring.

## Components

### 1. API Response Caching

**Location**: `backend/middleware/cache_middleware.py`

**Features**:
- Automatic GET request caching
- Redis-based storage
- Configurable TTL (default: 5 minutes)
- Path exclusion support
- Cache statistics

**Usage**:
```python
from backend.middleware import APICacheMiddleware

# Add to FastAPI app
app.add_middleware(
    APICacheMiddleware,
    default_ttl=300,  # 5 minutes
    exclude_paths=["/api/v1/health", "/api/v1/inference"]
)
```

**Custom Cache Control**:
```python
from backend.middleware import cache_response, no_cache

# Custom TTL
@app.get("/api/v1/projects")
@cache_response(ttl=600)  # 10 minutes
async def get_projects():
    ...

# Disable caching
@app.get("/api/v1/realtime")
@no_cache()
async def get_realtime_data():
    ...
```

### 2. Database Optimization

**Location**: `backend/core/database_optimization.py`

**Features**:
- Automatic index creation
- Table statistics analysis
- Query optimization
- VACUUM operations

**Usage**:
```python
from backend.core.database_optimization import get_optimizer

optimizer = get_optimizer()

# Create all indexes
results = optimizer.optimize_all()

# Vacuum database
optimizer.vacuum_database(full=False)

# Get slow queries
slow_queries = optimizer.get_slow_queries(limit=10)
```

**Indexes Created**:
- Projects: name, created_at, status
- Images: project_id, status, review_status
- Annotations: image_id, label_id, verified
- Datasets: project_id, split
- Training Jobs: status, dataset_id

### 3. Connection Pool Management

**Location**: `backend/core/pool_manager.py`

**Features**:
- Database connection pooling
- Redis connection pooling
- Pool statistics and monitoring
- Automatic connection recycling

**Configuration**:
```python
from backend.core.pool_manager import get_pool_manager

manager = get_pool_manager()

# Configure database pool
engine = manager.configure_db_pool(
    database_url="postgresql://...",
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600
)

# Configure Redis pool
redis_client = manager.configure_redis_pool(
    host="localhost",
    port=6379,
    max_connections=50
)

# Get pool stats
stats = manager.get_all_stats()
```

### 4. Performance Monitoring

**Location**: `backend/core/performance_monitor.py`

**Features**:
- Request timing
- System resource monitoring
- Per-endpoint statistics
- Slowest endpoint tracking

**Usage**:
```python
from backend.core.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# Record request
monitor.record_request(
    endpoint="/api/v1/projects",
    method="GET",
    duration=0.5,
    status_code=200
)

# Get metrics
summary = monitor.get_summary()
system_metrics = monitor.get_system_metrics()
slowest = monitor.get_slowest_endpoints(10)
```

### 5. Batch Operations

**Location**: `backend/utils/batch_operations.py`

**Features**:
- Optimized batch inserts
- Bulk updates
- Batch deletes
- Parallel processing

**Usage**:
```python
from backend.utils.batch_operations import batch_insert, batch_update

# Batch insert
data = [{"name": f"Project {i}"} for i in range(1000)]
batch_insert(session, Project, data, batch_size=100)

# Batch update
updates = [{"id": i, "status": "completed"} for i in range(1, 1001)]
batch_update(session, Project, updates, batch_size=100)

# Batch process
from backend.utils.batch_operations import batch_process

results = batch_process(
    items=image_list,
    processor=process_image_func,
    batch_size=50,
    parallel=True
)
```

## Performance Best Practices

### Database

1. **Use Indexes**: Ensure proper indexes on frequently queried columns
2. **Batch Operations**: Use bulk inserts/updates for large datasets
3. **Connection Pooling**: Configure appropriate pool sizes
4. **Query Optimization**: Use select_related() and joinedload()
5. **Pagination**: Always paginate large result sets

### Caching

1. **Cache Static Data**: Cache project configs, labels, etc.
2. **Set Appropriate TTL**: Balance freshness and performance
3. **Cache Invalidation**: Clear cache when data changes
4. **Use Redis**: Leverage Redis for distributed caching

### API

1. **Response Compression**: Enable gzip compression
2. **Rate Limiting**: Prevent abuse with rate limits
3. **Async Operations**: Use Celery for long-running tasks
4. **Pagination**: Implement cursor-based pagination

### System

1. **Resource Limits**: Set appropriate CPU/memory limits
2. **Worker Scaling**: Scale workers based on load
3. **Monitoring**: Track metrics and set alerts
4. **Load Balancing**: Distribute traffic across instances

## Benchmarking

**Tool**: `scripts/benchmark.py`

**Usage**:
```bash
python scripts/benchmark.py
```

**Custom Benchmarks**:
```python
from scripts.benchmark import benchmark_endpoint

result = benchmark_endpoint(
    endpoint="/api/v1/projects",
    requests_count=1000,
    concurrent=50
)
```

## Monitoring Endpoints

### Cache Statistics
```bash
GET /api/v1/cache/stats

Response:
{
  "enabled": true,
  "hits": 1500,
  "misses": 500,
  "hit_rate": 0.75,
  "total_requests": 2000
}
```

### Performance Metrics
```bash
GET /api/v1/performance/metrics

Response:
{
  "uptime_seconds": 3600,
  "system": {
    "cpu": {"percent": 45.2, "count": 8},
    "memory": {"percent": 62.5, "used": 8GB}
  },
  "requests": {
    "total_requests": 10000,
    "avg_response_time": 0.15,
    "error_rate": 0.02
  },
  "slowest_endpoints": [...]
}
```

### Pool Statistics
```bash
GET /api/v1/pools/stats

Response:
{
  "database_pool": {
    "size": 20,
    "checked_out": 5,
    "overflow": 2
  },
  "redis_pool": {
    "max_connections": 50,
    "in_use_connections": 12
  }
}
```

## Optimization Checklist

- [ ] Enable API response caching
- [ ] Create database indexes
- [ ] Configure connection pools
- [ ] Enable query logging (development)
- [ ] Set up performance monitoring
- [ ] Run ANALYZE on tables
- [ ] Optimize slow queries
- [ ] Enable gzip compression
- [ ] Configure rate limiting
- [ ] Scale workers appropriately
- [ ] Set resource limits
- [ ] Monitor system metrics
- [ ] Benchmark critical endpoints
- [ ] Profile slow operations

## Troubleshooting

### High Database Load
- Check for missing indexes
- Review slow query log
- Optimize N+1 queries
- Increase connection pool size

### High Memory Usage
- Check for memory leaks
- Review connection pool sizes
- Monitor cache sizes
- Scale horizontally

### Slow API Responses
- Enable caching
- Review database queries
- Check for blocking operations
- Profile with performance monitor

### Cache Issues
- Verify Redis connectivity
- Check cache hit rate
- Review TTL settings
- Monitor cache size

## Further Reading

- [Database Optimization](./DATABASE_OPTIMIZATION.md)
- [Caching Strategy](./CACHING_STRATEGY.md)
- [Monitoring Guide](./MONITORING_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
