"""
数据库连接管理
Database Connection Management

提供SQLAlchemy引擎和会话管理
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from backend.core.config import settings
from backend.core.logging import logger


# SQLAlchemy Base
Base = declarative_base()


# 创建数据库引擎
def create_db_engine():
    """创建数据库引擎"""
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,  # 连接池预检查
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,  # 1小时回收连接
    )
    
    # 添加事件监听器
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """连接建立时的回调"""
        logger.debug("Database connection established")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """从连接池取出连接时的回调"""
        logger.debug("Connection checked out from pool")
    
    return engine


# 创建引擎
engine = create_db_engine()


# 创建Session工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话 (用于FastAPI依赖注入)
    
    用法:
        from fastapi import Depends
        from backend.core.database import get_db
        
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话 (用于上下文管理器)
    
    用法:
        from backend.core.database import get_db_context
        
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表(如果不存在)
    """
    logger.info("Initializing database...")
    
    # 导入所有模型(确保Base.metadata包含所有表)
    import backend.models  # noqa: F401
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")


def check_db_connection() -> bool:
    """
    检查数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def close_db():
    """关闭数据库连接"""
    logger.info("Closing database connections...")
    engine.dispose()
    logger.info("Database connections closed")


if __name__ == "__main__":
    # 测试数据库连接
    print("Testing database connection...")
    
    if check_db_connection():
        print("✅ Database connection successful!")
        
        # 测试会话
        with get_db_context() as db:
            result = db.execute("SELECT version()")
            version = result.scalar()
            print(f"PostgreSQL version: {version}")
    else:
        print("❌ Database connection failed!")
