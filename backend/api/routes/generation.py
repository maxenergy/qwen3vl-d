"""
图片生成API路由
Generation API Routes
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.api.dependencies import (
    get_db_session,
    get_project_or_404,
    get_pagination_params,
)
from backend.core.logging import logger
from backend.models.project import Project
from backend.models.generation import GenerationTask, Image as ImageModel
from backend.schemas.generation import (
    GenerationTaskCreate,
    GenerationTaskResponse,
    GenerationTaskListItem,
    ImageResponse,
    BatchGenerationRequest,
    TemplateListResponse,
    TemplateResponse,
)
from backend.schemas.common import PagedResponse
from backend.services.hunyuan_generator import HunyuanImageGenerator
from backend.services.prompt_template import template_manager


router = APIRouter()


@router.post("/projects/{project_id}/generation/tasks", status_code=201)
async def create_generation_task(
    project_id: int,
    task_data: GenerationTaskCreate,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> GenerationTaskResponse:
    """
    创建图片生成任务

    - **project_id**: 项目ID
    - **task_data**: 任务配置
    """
    try:
        # 如果使用了模板，渲染模板
        prompt = task_data.prompt
        negative_prompt = task_data.negative_prompt or ""
        params = task_data.params or {}

        if task_data.template_name:
            try:
                rendered = template_manager.render_template(
                    task_data.template_name,
                    description=task_data.prompt,
                )
                prompt = rendered["prompt"]
                negative_prompt = rendered["negative_prompt"]
                # 合并模板参数和用户参数，用户参数优先
                params = {**rendered["params"], **params}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        # 创建生成任务
        task = GenerationTask(
            project_id=project_id,
            name=task_data.name,
            prompt=prompt,
            negative_prompt=negative_prompt,
            mode=task_data.mode,
            resolution=task_data.resolution,
            batch_size=task_data.batch_size,
            params=params,
            status="pending",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"Created generation task {task.id} for project {project_id}")

        # 使用Celery异步执行图片生成
        from backend.tasks.generation import execute_generation_task as celery_generate_task
        celery_generate_task.delay(task.id)

        return GenerationTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create generation task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/projects/{project_id}/generation/tasks")
async def list_generation_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="任务状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[GenerationTaskListItem]:
    """
    列出项目的生成任务

    - **project_id**: 项目ID
    - **status**: 状态筛选 (pending, processing, completed, failed)
    - **page**: 页码
    - **per_page**: 每页数量
    """
    try:
        query = db.query(GenerationTask).filter(GenerationTask.project_id == project_id)

        # 状态筛选
        if status:
            query = query.filter(GenerationTask.status == status)

        # 总数
        total = query.count()

        # 分页查询
        tasks = (
            query.order_by(desc(GenerationTask.created_at))
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        # 计算每个任务的统计信息
        items = []
        for task in tasks:
            # 统计生成的图片
            images_count = (
                db.query(ImageModel)
                .filter(ImageModel.generation_task_id == task.id)
                .count()
            )

            # 统计已审核的图片
            approved_count = (
                db.query(ImageModel)
                .filter(
                    ImageModel.generation_task_id == task.id,
                    ImageModel.review_status == "approved",
                )
                .count()
            )

            item = GenerationTaskListItem(
                id=task.id,
                project_id=task.project_id,
                name=task.name,
                status=task.status,
                mode=task.mode,
                resolution=task.resolution,
                batch_size=task.batch_size,
                created_at=task.created_at,
                updated_at=task.updated_at,
                progress=task.progress or 0,
                images_generated=images_count,
                images_approved=approved_count,
            )
            items.append(item)

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list generation tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/generation/tasks/{task_id}")
async def get_generation_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> GenerationTaskResponse:
    """
    获取生成任务详情

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(GenerationTask)
        .filter(
            GenerationTask.id == task_id,
            GenerationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Generation task not found")

    return GenerationTaskResponse.model_validate(task)


@router.delete("/projects/{project_id}/generation/tasks/{task_id}", status_code=204)
async def delete_generation_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除生成任务

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(GenerationTask)
        .filter(
            GenerationTask.id == task_id,
            GenerationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Generation task not found")

    # 只能删除已完成或失败的任务
    if task.status in ["processing", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete task in progress",
        )

    try:
        # 删除关联的图片记录（实际文件需要单独处理）
        db.query(ImageModel).filter(ImageModel.generation_task_id == task_id).delete()

        db.delete(task)
        db.commit()

        logger.info(f"Deleted generation task {task_id}")

    except Exception as e:
        logger.error(f"Failed to delete generation task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/generation/tasks/{task_id}/images")
async def list_generated_images(
    project_id: int,
    task_id: int,
    review_status: Optional[str] = Query(None, description="审核状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[ImageResponse]:
    """
    列出任务生成的图片

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    - **review_status**: 审核状态筛选 (pending, approved, rejected)
    """
    # 验证任务存在
    task = (
        db.query(GenerationTask)
        .filter(
            GenerationTask.id == task_id,
            GenerationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Generation task not found")

    try:
        query = db.query(ImageModel).filter(ImageModel.generation_task_id == task_id)

        # 审核状态筛选
        if review_status:
            query = query.filter(ImageModel.review_status == review_status)

        # 总数
        total = query.count()

        # 分页查询
        images = (
            query.order_by(ImageModel.created_at)
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [ImageResponse.model_validate(img) for img in images]

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except Exception as e:
        logger.error(f"Failed to list generated images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/generation/batch", status_code=201)
async def batch_generate(
    project_id: int,
    request_data: BatchGenerationRequest,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> List[GenerationTaskResponse]:
    """
    批量创建生成任务

    - **project_id**: 项目ID
    - **request_data**: 批量请求数据
    """
    try:
        tasks = []

        for i, prompt in enumerate(request_data.prompts):
            # 创建任务
            task = GenerationTask(
                project_id=project_id,
                name=f"{request_data.name_prefix}_{i+1}" if request_data.name_prefix else f"Batch_{i+1}",
                prompt=prompt,
                negative_prompt=request_data.negative_prompt or "",
                mode=request_data.mode,
                resolution=request_data.resolution,
                batch_size=1,  # 批量时每个任务生成1张
                params=request_data.params or {},
                status="pending",
            )

            db.add(task)
            tasks.append(task)

        db.commit()

        # 刷新所有任务
        from backend.tasks.generation import execute_generation_task as celery_generate_task
        for task in tasks:
            db.refresh(task)
            # 使用Celery异步执行
            celery_generate_task.delay(task.id)

        logger.info(f"Created {len(tasks)} batch generation tasks for project {project_id}")

        return [GenerationTaskResponse.model_validate(task) for task in tasks]

    except Exception as e:
        logger.error(f"Failed to create batch tasks: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    tags: Optional[str] = Query(None, description="标签筛选（逗号分隔）"),
) -> TemplateListResponse:
    """
    列出所有提示词模板

    - **category**: 分类筛选
    - **keyword**: 关键词搜索（搜索名称和描述）
    - **tags**: 标签筛选（逗号分隔）
    """
    try:
        # 解析标签
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # 搜索模板
        templates = template_manager.search_templates(
            keyword=keyword,
            category=category,
            tags=tag_list,
        )

        # 转换为响应格式
        items = [
            TemplateResponse(
                name=t.name,
                category=t.category,
                prompt=t.prompt,
                negative_prompt=t.negative_prompt,
                params=t.params,
                tags=t.tags,
                description=t.description,
            )
            for t in templates
        ]

        return TemplateListResponse(
            total=len(items),
            categories=template_manager.list_categories(),
            templates=items,
        )

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}")
async def get_template(
    template_name: str,
) -> TemplateResponse:
    """
    获取指定模板详情

    - **template_name**: 模板名称
    """
    template = template_manager.get_template(template_name)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse(
        name=template.name,
        category=template.category,
        prompt=template.prompt,
        negative_prompt=template.negative_prompt,
        params=template.params,
        tags=template.tags,
        description=template.description,
    )


# Note: Background task execution has been moved to backend/tasks/generation.py
# using Celery for better scalability and reliability
