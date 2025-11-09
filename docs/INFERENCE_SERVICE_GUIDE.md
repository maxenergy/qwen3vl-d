# Inference Service Guide

Complete guide for the AI Auto-Annotation Tool's inference service, powered by Qwen3-VL model.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Model Management](#model-management)
- [Caching](#caching)
- [Monitoring](#monitoring)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Overview

The inference service provides automatic image annotation capabilities using the Qwen3-VL vision-language model. It supports:

- **Real-time inference** for single images
- **Batch processing** for multiple images
- **Asynchronous tasks** using Celery
- **Result caching** with Redis
- **Performance monitoring** and metrics
- **Multi-model support** with hot-swapping

### Key Features

✅ **GPU Acceleration** - Automatic GPU detection and utilization
✅ **Smart Caching** - Redis-based result caching for improved performance
✅ **Load Balancing** - Support for multiple model instances
✅ **Real-time Monitoring** - Comprehensive metrics and health checks
✅ **Flexible Tasks** - Detection and segmentation support

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Inference Service                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │   Model      │    │  Inference   │    │   Cache     │  │
│  │   Manager    │◄──►│   Service    │◄──►│   Service   │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
│         │                    │                    │         │
│         │                    │                    │         │
│  ┌──────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐  │
│  │   Qwen3-VL  │      │   Celery   │      │   Redis    │  │
│  │    Model    │      │   Worker   │      │   Cache    │  │
│  └─────────────┘      └────────────┘      └────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Components

1. **Model Manager** - Handles model loading, caching, and lifecycle
2. **Inference Service** - Core inference logic and processing
3. **Cache Service** - Redis-based result caching
4. **Monitoring Service** - Metrics collection and health checks
5. **Celery Tasks** - Asynchronous processing for batch operations

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (for caching)
docker-compose up -d redis

# Start Celery worker (for async tasks)
celery -A backend.worker worker --loglevel=info
```

### Basic Usage

#### 1. Single Image Inference (Python)

```python
from backend.services.inference_service import get_inference_service

# Get service
service = get_inference_service()

# Perform inference
result = service.infer_single(
    image_path="/path/to/image.jpg",
    labels=["car", "person", "bicycle"],
    confidence_threshold=0.5
)

# Access results
print(f"Found {len(result.annotations)} annotations")
for ann in result.annotations:
    print(f"  - {ann['label']}: {ann['confidence']:.2f}")
```

#### 2. Single Image Inference (API)

```bash
curl -X POST "http://localhost:8000/api/v1/inference/infer" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/storage/images/sample.jpg",
    "labels": ["car", "person", "bicycle"],
    "confidence_threshold": 0.5
  }'
```

Response:
```json
{
  "image_path": "/storage/images/sample.jpg",
  "annotations": [
    {
      "label": "car",
      "confidence": 0.95,
      "bbox": [10, 20, 100, 150],
      "type": "detection"
    }
  ],
  "inference_time": 1.5,
  "model_name": "Qwen/Qwen3-VL-2B-Instruct",
  "model_version": "default",
  "confidence_threshold": 0.5,
  "timestamp": "2024-01-01T12:00:00",
  "annotation_count": 1
}
```

#### 3. Batch Inference

```python
# Batch processing
results = service.infer_batch(
    image_paths=[
        "/path/to/image1.jpg",
        "/path/to/image2.jpg",
        "/path/to/image3.jpg"
    ],
    labels=["car", "person"],
    confidence_threshold=0.6
)

print(f"Processed {len(results)} images")
```

#### 4. Asynchronous Inference

```python
from backend.tasks.inference_tasks import infer_single_task

# Submit async task
task = infer_single_task.delay(
    image_path="/path/to/image.jpg",
    labels=["car", "person"],
    confidence_threshold=0.5
)

# Check status
print(f"Task ID: {task.id}")
print(f"Status: {task.state}")

# Get result (blocks until complete)
result = task.get()
```

## API Reference

### Inference Endpoints

#### POST /api/v1/inference/infer

Perform inference on a single image.

**Request Body:**
```json
{
  "image_path": "/path/to/image.jpg",
  "labels": ["car", "person"],
  "confidence_threshold": 0.5,
  "model_name": null,
  "model_version": "default",
  "task_type": "detection"
}
```

**Response:** InferenceResponse object

---

#### POST /api/v1/inference/infer/batch

Perform batch inference on multiple images.

**Request Body:**
```json
{
  "image_paths": ["/path/1.jpg", "/path/2.jpg"],
  "labels": ["car", "person"],
  "confidence_threshold": 0.5
}
```

**Response:**
```json
{
  "results": [...],
  "total_images": 2,
  "successful": 2,
  "failed": 0,
  "total_time": 3.5
}
```

---

#### POST /api/v1/inference/infer/upload

Upload and infer an image.

**Form Data:**
- `file`: Image file (multipart/form-data)
- `labels`: Comma-separated labels
- `confidence_threshold`: Float (0.0-1.0)

---

### Model Management Endpoints

#### GET /api/v1/inference/models

List all loaded models.

**Response:**
```json
{
  "models": {
    "Qwen/Qwen3-VL-2B-Instruct:default": {
      "name": "Qwen/Qwen3-VL-2B-Instruct",
      "version": "default",
      "device": "cuda:0",
      "loaded": true,
      "loaded_at": "2024-01-01T12:00:00",
      "last_used_at": "2024-01-01T12:05:00",
      "use_count": 42
    }
  }
}
```

---

#### POST /api/v1/inference/models/load

Load a model into memory.

**Query Parameters:**
- `model_name`: Model identifier
- `model_version`: Version (default: "default")
- `force_reload`: Boolean (default: false)

---

#### DELETE /api/v1/inference/models/{model_name}

Unload a model from memory.

---

### Statistics Endpoints

#### GET /api/v1/inference/stats

Get basic inference statistics.

**Response:**
```json
{
  "total_inferences": 100,
  "total_images": 100,
  "total_inference_time": 150.0,
  "avg_inference_time": 1.5,
  "errors": 5
}
```

---

#### GET /api/v1/inference/metrics

Get detailed metrics.

**Response:**
```json
{
  "summary": {
    "uptime_seconds": 3600,
    "total_requests": 100,
    "success_rate": 0.95,
    "requests_per_second": 0.027,
    "cache": {
      "hits": 20,
      "misses": 80,
      "hit_rate": 0.2
    },
    "inference_time": {
      "avg": 1.5,
      "min": 0.8,
      "max": 3.2
    }
  },
  "models": {...},
  "labels": {...},
  "recent_errors": [...]
}
```

---

#### GET /api/v1/inference/health

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": 1,
  "cache_available": true,
  "success_rate": 0.95,
  "requests_per_second": 10.0,
  "last_request": "2024-01-01T12:00:00"
}
```

## Model Management

### Loading Models

```python
from backend.services.model_manager import get_model_manager

manager = get_model_manager()

# Load default model
model_info = manager.get_default_model()

# Load specific model
model_info = manager.load_model(
    model_name="Qwen/Qwen3-VL-2B-Instruct",
    version="1.0"
)

# Force reload
model_info = manager.load_model(
    model_name="Qwen/Qwen3-VL-2B-Instruct",
    force_reload=True
)
```

### Model Information

```python
# Get model stats
stats = model_info.get_stats()
print(f"Model: {stats['name']}")
print(f"Device: {stats['device']}")
print(f"Use count: {stats['use_count']}")
```

### Unloading Models

```python
# Unload specific model
success = manager.unload_model("Qwen/Qwen3-VL-2B-Instruct", "1.0")

# This frees GPU memory
```

## Caching

### Cache Configuration

Configure caching in `configs/config.yaml`:

```yaml
redis:
  enabled: true
  host: localhost
  port: 6379
  db: 0
  password: null
```

### Cache Behavior

- **Cache Key**: Generated from image path, labels, threshold, model info
- **TTL**: 1 hour (configurable)
- **Invalidation**: Automatic on TTL expiration

### Manual Cache Control

```python
from backend.services.inference_cache import get_inference_cache

cache = get_inference_cache()

# Get cached result
result = cache.get(
    image_path="/path/to/image.jpg",
    labels=["car"],
    confidence_threshold=0.5,
    model_name="test-model",
    model_version="1.0"
)

# Delete cached result
cache.delete(
    image_path="/path/to/image.jpg",
    labels=["car"],
    confidence_threshold=0.5,
    model_name="test-model",
    model_version="1.0"
)

# Clear all cache
cache.clear_all()

# Get cache stats
stats = cache.get_stats()
```

## Monitoring

### Real-time Metrics

```python
from backend.services.inference_monitor import get_inference_monitor

monitor = get_inference_monitor()

# Get all metrics
metrics = monitor.get_metrics()

# Summary statistics
summary = metrics['summary']
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Avg inference time: {summary['inference_time']['avg']:.2f}s")

# Per-model metrics
for model, stats in metrics['models'].items():
    print(f"{model}: {stats['requests']} requests")

# Per-label metrics
for label, stats in metrics['labels'].items():
    print(f"{label}: {stats['detections']} detections")
```

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/api/v1/inference/health

# Get detailed metrics
curl http://localhost:8000/api/v1/inference/metrics
```

## Performance Tuning

### GPU Optimization

```yaml
# config.yaml
model:
  device_id: 0  # GPU device
  max_new_tokens: 512
  batch_size: 8
```

### Batch Size Tuning

```python
# Larger batches = better throughput
results = service.infer_batch(
    image_paths=image_list,
    labels=labels
)
```

### Caching Strategy

```python
# Enable caching for repeated queries
result = service.infer_single(
    image_path=path,
    labels=labels,
    use_cache=True  # Default
)
```

### Async Processing

```python
# Use Celery for long-running tasks
from backend.tasks.inference_tasks import infer_batch_task

task = infer_batch_task.delay(
    image_paths=large_image_list,
    labels=labels
)
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory (GPU)

**Symptom:** CUDA out of memory error

**Solution:**
```python
# Reduce batch size
# Unload unused models
manager.unload_model("old-model")

# Or use CPU
# Set model.device_id = -1 in config
```

#### 2. Slow Inference

**Symptom:** High inference times

**Solutions:**
- Enable GPU acceleration
- Use caching for repeated queries
- Process in batches
- Check model is loaded (not loading each time)

#### 3. Cache Not Working

**Symptom:** Cache misses every time

**Solutions:**
```bash
# Check Redis connection
redis-cli ping

# Check cache stats
curl http://localhost:8000/api/v1/inference/metrics
```

#### 4. Model Load Failures

**Symptom:** Model fails to load

**Solutions:**
- Check model path in config
- Verify HuggingFace token (if needed)
- Check disk space
- Review logs for specific errors

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# This will show detailed inference logs
```

### Performance Benchmarking

```python
import time

# Benchmark inference
start = time.time()
result = service.infer_single(image_path, labels)
elapsed = time.time() - start

print(f"Inference time: {elapsed:.2f}s")
```

## Best Practices

1. **Pre-load Models** - Load models at startup to avoid first-request delays
2. **Use Caching** - Enable caching for production workloads
3. **Monitor Metrics** - Set up monitoring dashboards
4. **Batch When Possible** - Use batch inference for multiple images
5. **Async for Large Jobs** - Use Celery tasks for large datasets
6. **Unload Unused Models** - Free memory when switching models

## API Client Examples

### Python Client

```python
import requests

class InferenceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def infer(self, image_path, labels, threshold=0.5):
        response = requests.post(
            f"{self.base_url}/api/v1/inference/infer",
            json={
                "image_path": image_path,
                "labels": labels,
                "confidence_threshold": threshold
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = InferenceClient()
result = client.infer("/path/to/image.jpg", ["car", "person"])
```

### JavaScript Client

```javascript
async function inferImage(imagePath, labels) {
  const response = await fetch('/api/v1/inference/infer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      image_path: imagePath,
      labels: labels,
      confidence_threshold: 0.5
    })
  });

  return await response.json();
}

// Usage
const result = await inferImage('/path/to/image.jpg', ['car', 'person']);
console.log(`Found ${result.annotation_count} annotations`);
```

## Further Reading

- [Qwen3-VL Model Documentation](https://huggingface.co/Qwen/Qwen3-VL)
- [Model Configuration Guide](./CONFIGURATION_GUIDE.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

## Support

For issues or questions:
- GitHub Issues: [qwen3vl-d/issues](https://github.com/your-org/qwen3vl-d/issues)
- Documentation: [docs/](../docs/)
