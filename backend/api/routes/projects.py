"""
项目管理路由
Projects Routes

处理项目和标签的CRUD操作
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db_session, get_pagination_params, get_project_or_404
from backend.core.logging import logger
from backend.models import Label, Project
from backend.schemas import (
    LabelCreate,
    LabelResponse,
    LabelUpdate,
    PagedResponse,
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
    SuccessResponse,
)


router = APIRouter()


# ============ 项目CRUD ============

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db_session)
):
    """
    创建新项目
    
    - **name**: 项目名称（唯一，至少3个字符）
    - **description**: 项目描述（可选）
    - **labels**: 初始标签列表（可选）
    """
    # 检查项目名称是否已存在
    existing = db.query(Project).filter(Project.name == project_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with name '{project_data.name}' already exists"
        )
    
    # 创建项目
    project = Project(
        name=project_data.name,
        description=project_data.description
    )
    
    db.add(project)
    db.flush()  # 获取project.id
    
    # 创建初始标签
    if project_data.labels:
        for label_data in project_data.labels:
            label = Label(
                project_id=project.id,
                name=label_data.name,
                color=label_data.color,
                description=label_data.description
            )
            db.add(label)
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"Created project: {project.name} (id={project.id})")
    
    return project


@router.get("/projects", response_model=PagedResponse[ProjectListItem])
async def list_projects(
    status_filter: str = None,
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session)
):
    """
    获取项目列表（分页）
    
    - **page**: 页码（默认1）
    - **per_page**: 每页数量（默认20，最大100）
    - **status**: 过滤状态：active, archived
    """
    # 构建查询
    query = db.query(Project)
    
    # 状态过滤
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    # 总数
    total = query.count()
    
    # 分页
    projects = query.order_by(Project.created_at.desc()) \
        .offset(pagination["skip"]) \
        .limit(pagination["per_page"]) \
        .all()
    
    # 计算统计信息
    items = []
    for project in projects:
        label_count = db.query(Label).filter(Label.project_id == project.id).count()
        
        item = ProjectListItem(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            label_count=label_count,
            image_count=0,  # TODO: 计算图片数量
            annotation_count=0  # TODO: 计算标注数量
        )
        items.append(item)
    
    # 计算总页数
    pages = (total + pagination["per_page"] - 1) // pagination["per_page"]
    
    return PagedResponse(
        total=total,
        page=pagination["page"],
        per_page=pagination["per_page"],
        pages=pages,
        items=items
    )


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db_session)
):
    """
    获取项目详情
    
    返回项目的完整信息，包括标签、版本、统计等
    """
    # 构建统计信息
    statistics = {
        "total_images": 0,  # TODO
        "approved_images": 0,  # TODO
        "total_annotations": 0,  # TODO
        "models_trained": 0  # TODO
    }
    
    # TODO: 获取数据集版本列表
    versions = []
    
    return ProjectDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        labels=[LabelResponse.model_validate(label) for label in project.labels],
        statistics=statistics,
        versions=versions
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_data: ProjectUpdate,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db_session)
):
    """
    更新项目
    
    可更新的字段：
    - description
    - status
    - settings
    """
    # 更新字段
    if project_data.description is not None:
        project.description = project_data.description
    
    if project_data.status is not None:
        project.status = project_data.status
    
    if project_data.settings is not None:
        project.settings = project_data.settings
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"Updated project: {project.name} (id={project.id})")
    
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db_session)
):
    """
    删除项目（软删除）
    
    将项目状态标记为deleted，不实际删除数据
    """
    project.status = "deleted"
    db.commit()
    
    logger.info(f"Deleted project: {project.name} (id={project.id})")
    
    # 204 No Content不返回任何内容
    return None


# ============ 标签管理 ============

@router.post("/projects/{project_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def add_label(
    label_data: LabelCreate,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db_session)
):
    """
    为项目添加标签
    """
    # 检查标签名称是否已存在
    existing = db.query(Label).filter(
        Label.project_id == project.id,
        Label.name == label_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Label '{label_data.name}' already exists in this project"
        )
    
    # 创建标签
    label = Label(
        project_id=project.id,
        name=label_data.name,
        color=label_data.color,
        description=label_data.description
    )
    
    db.add(label)
    db.commit()
    db.refresh(label)
    
    logger.info(f"Added label: {label.name} to project {project.name}")
    
    return label


@router.get("/projects/{project_id}/labels", response_model=List[LabelResponse])
async def list_labels(
    project: Project = Depends(get_project_or_404),
    include_inactive: bool = False,
    db: Session = Depends(get_db_session)
):
    """
    获取项目的所有标签
    
    - **include_inactive**: 是否包含已禁用的标签
    """
    query = db.query(Label).filter(Label.project_id == project.id)
    
    if not include_inactive:
        query = query.filter(Label.is_active == True)
    
    labels = query.order_by(Label.created_at).all()
    
    return labels


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    label_data: LabelUpdate,
    db: Session = Depends(get_db_session)
):
    """
    更新标签
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found"
        )
    
    # 更新字段
    if label_data.name is not None:
        label.name = label_data.name
    
    if label_data.color is not None:
        label.color = label_data.color
    
    if label_data.description is not None:
        label.description = label_data.description
    
    if label_data.is_active is not None:
        label.is_active = label_data.is_active
    
    db.commit()
    db.refresh(label)
    
    logger.info(f"Updated label: {label.name} (id={label.id})")
    
    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    db: Session = Depends(get_db_session)
):
    """
    删除标签
    
    警告：会级联删除所有使用该标签的标注
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found"
        )
    
    label_name = label.name
    db.delete(label)
    db.commit()
    
    logger.warning(f"Deleted label: {label_name} (id={label_id})")
    
    return None


# 导出router
__all__ = ["router"]
