# Multi-stage Dockerfile for AI Auto-Annotation Tool Backend

# Stage 1: Base image with Python dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# Stage 2: Development image
FROM base as development

# Install development tools
RUN pip install pytest pytest-cov pytest-asyncio black isort flake8

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Command for development
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Stage 3: Production image
FROM base as production

# Copy application code
COPY --chown=appuser:appuser . .

# Install application in production mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/storage/images /app/storage/datasets /app/storage/models /app/logs && \
    chown -R appuser:appuser /app/storage /app/logs

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


# Stage 4: Celery worker image
FROM production as celery-worker

# Override command for Celery worker
CMD ["celery", "-A", "backend.tasks.celery_app", "worker", \
     "-Q", "generation,annotation,dataset,training", \
     "--loglevel=info", \
     "--concurrency=4"]
