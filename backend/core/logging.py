"""
日志配置模块
Logging Configuration

使用Loguru进行结构化日志
"""

import sys
from pathlib import Path

from loguru import logger

from backend.core.config import settings


# 移除默认handler
logger.remove()


# 控制台输出handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)


# 文件输出handler
log_file = Path(settings.log_file)
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_file),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    rotation="100 MB",  # 文件大小达到100MB时轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
)


# 错误日志单独文件
error_log_file = log_file.parent / "error.log"
logger.add(
    str(error_log_file),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="50 MB",
    retention="60 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,  # 显示完整traceback
    diagnose=True,  # 显示变量值
)


def get_logger(name: str = None):
    """
    获取logger实例
    
    Args:
        name: logger名称
    
    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger


# 导出默认logger
__all__ = ["logger", "get_logger"]


if __name__ == "__main__":
    # 测试日志
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # 测试异常日志
    try:
        1 / 0
    except Exception as e:
        logger.exception("An exception occurred")
