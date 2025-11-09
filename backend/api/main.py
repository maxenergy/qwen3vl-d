"""
FastAPI主应用
FastAPI Main Application

自动标注工具的API入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.database import check_db_connection, close_db
from backend.core.logging import logger
from backend.schemas import ErrorDetail, HealthResponse


# ============ 生命周期管理 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时执行初始化，关闭时清理资源
    """
    # 启动时
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)
    
    # 检查数据库连接
    if not check_db_connection():
        logger.error("Database connection failed! Please check your configuration.")
    else:
        logger.info("Database connection successful")
    
    # TODO: 初始化其他服务（Redis, Celery等）
    
    logger.info("Application startup complete")
    
    yield
    
    # 关闭时
    logger.info("Shutting down application...")
    close_db()
    logger.info("Application shutdown complete")


# ============ 创建FastAPI应用 ============

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于Hunyuan Image 3.0和Qwen3-VL的自动数据集生成与标注系统",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# ============ 中间件配置 ============

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============ 异常处理器 ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    捕获所有未处理的异常并返回统一格式的错误响应
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred",
        details={"error": str(exc)} if settings.debug else None
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error.model_dump()}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """ValueError异常处理器"""
    logger.warning(f"ValueError: {exc}")
    
    error = ErrorDetail(
        code="VALIDATION_ERROR",
        message=str(exc)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": error.model_dump()}
    )


# ============ 基础路由 ============

@app.get("/", tags=["Root"])
async def root():
    """根路径，返回API基本信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    健康检查端点
    
    检查各个服务的状态
    """
    # 检查数据库
    db_status = "ok" if check_db_connection() else "error"
    
    # TODO: 检查Redis
    redis_status = "not_implemented"
    
    # TODO: 检查Celery
    celery_status = "not_implemented"
    
    # TODO: 检查Hunyuan
    hunyuan_status = "not_implemented"
    
    # TODO: 检查Qwen3-VL
    qwen3vl_status = "not_implemented"
    
    services = {
        "database": db_status,
        "redis": redis_status,
        "celery": celery_status,
        "hunyuan": hunyuan_status,
        "qwen3vl": qwen3vl_status,
    }
    
    # 如果关键服务有问题，返回unhealthy
    overall_status = "healthy" if db_status == "ok" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        services=services,
        version=settings.app_version
    )


# ============ 注册API路由 ============

# 导入并注册路由模块
from backend.api.routes import projects, generation, images, annotation, datasets

app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(generation.router, prefix="/api/v1", tags=["Generation"])
app.include_router(images.router, prefix="/api/v1", tags=["Images"])
app.include_router(annotation.router, prefix="/api/v1", tags=["Annotation"])
app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])

# TODO: 其他路由模块待实现
# from backend.api.routes import training, models
# app.include_router(training.router, prefix="/api/v1", tags=["Training"])
# app.include_router(models.router, prefix="/api/v1", tags=["Models"])


# ============ 开发服务器 ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
