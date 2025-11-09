"""
API依赖注入
API Dependencies

提供可复用的依赖项用于路由处理器
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.logging import logger
from backend.models import Project


# ============ 数据库会话依赖 ============

def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI路由中注入数据库会话
    """
    return get_db()


# ============ 项目验证依赖 ============

def get_project_or_404(
    project_id: int,
    db: Session = Depends(get_db_session)
) -> Project:
    """
    获取项目或返回404
    
    Args:
        project_id: 项目ID
        db: 数据库会话
        
    Returns:
        Project对象
        
    Raises:
        HTTPException: 项目不存在时抛出404
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return project


# ============ 分页参数依赖 ============

def get_pagination_params(
    page: int = 1,
    per_page: int = 20
) -> dict:
    """
    获取分页参数
    
    Args:
        page: 页码(默认1)
        per_page: 每页数量(默认20, 最大100)
        
    Returns:
        包含page, per_page, skip的字典
    """
    # 验证参数
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page must be >= 1"
        )
    
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Per page must be between 1 and 100"
        )
    
    skip = (page - 1) * per_page
    
    return {
        "page": page,
        "per_page": per_page,
        "skip": skip
    }


# ============ 认证依赖(预留) ============

def get_current_user():
    """
    获取当前用户(预留功能)
    
    MVP版本暂不实现认证
    """
    # TODO: 实现JWT认证
    pass


# 导出
__all__ = [
    "get_db_session",
    "get_project_or_404",
    "get_pagination_params",
    "get_current_user",
]
