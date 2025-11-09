"""
标注API路由
Annotation API Routes

自动标注任务管理和标注结果处理
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
from backend.models.annotation import AnnotationTask, Annotation
from backend.models.generation import Image as ImageModel
from backend.schemas.annotation import (
    AnnotationTaskCreate,
    AnnotationTaskResponse,
    AnnotationTaskListItem,
    AnnotationResponse,
    AnnotationReviewRequest,
    BatchAnnotationRequest,
)
from backend.schemas.common import PagedResponse


router = APIRouter()


@router.post("/projects/{project_id}/annotation/tasks", status_code=201)
async def create_annotation_task(
    project_id: int,
    task_data: AnnotationTaskCreate,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> AnnotationTaskResponse:
    """
    创建标注任务

    - **project_id**: 项目ID
    - **task_data**: 任务配置
    """
    try:
        # 验证图片存在
        images_count = (
            db.query(ImageModel)
            .filter(
                ImageModel.id.in_(task_data.image_ids),
                ImageModel.project_id == project_id,
            )
            .count()
        )

        if images_count != len(task_data.image_ids):
            raise HTTPException(
                status_code=404,
                detail="Some images not found or don't belong to this project",
            )

        # 验证标签存在
        from backend.models.project import Label

        labels_count = (
            db.query(Label)
            .filter(
                Label.id.in_(task_data.label_ids),
                Label.project_id == project_id,
                Label.is_active == True,
            )
            .count()
        )

        if labels_count != len(task_data.label_ids):
            raise HTTPException(
                status_code=404,
                detail="Some labels not found or are inactive",
            )

        # 创建标注任务
        task = AnnotationTask(
            project_id=project_id,
            name=task_data.name,
            description=task_data.description,
            model_config={
                "model": task_data.model or "qwen3-vl-30b",
                "confidence_threshold": task_data.confidence_threshold,
                "prompt_template": task_data.prompt_template,
            },
            status="pending",
        )

        db.add(task)
        db.flush()  # 获取task.id

        # 关联图片和标签
        task.image_ids = task_data.image_ids
        task.label_ids = task_data.label_ids

        db.commit()
        db.refresh(task)

        logger.info(f"Created annotation task {task.id} for project {project_id}")

        # 使用Celery异步执行标注
        from backend.tasks.annotation import execute_annotation_task
        execute_annotation_task.delay(task.id)

        return AnnotationTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create annotation task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/projects/{project_id}/annotation/tasks")
async def list_annotation_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="任务状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[AnnotationTaskListItem]:
    """
    列出项目的标注任务

    - **project_id**: 项目ID
    - **status**: 状态筛选 (pending, processing, completed, failed)
    - **page**: 页码
    - **per_page**: 每页数量
    """
    try:
        query = db.query(AnnotationTask).filter(AnnotationTask.project_id == project_id)

        # 状态筛选
        if status:
            query = query.filter(AnnotationTask.status == status)

        # 总数
        total = query.count()

        # 分页查询
        tasks = (
            query.order_by(desc(AnnotationTask.created_at))
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        # 计算每个任务的统计信息
        items = []
        for task in tasks:
            # 统计标注数量
            annotations_count = (
                db.query(Annotation)
                .filter(Annotation.annotation_task_id == task.id)
                .count()
            )

            # 统计已审核数量
            reviewed_count = (
                db.query(Annotation)
                .filter(
                    Annotation.annotation_task_id == task.id,
                    Annotation.review_status.in_(["approved", "rejected"]),
                )
                .count()
            )

            item = AnnotationTaskListItem(
                id=task.id,
                project_id=task.project_id,
                name=task.name,
                status=task.status,
                created_at=task.created_at,
                updated_at=task.updated_at,
                progress=task.progress or 0,
                total_images=len(task.image_ids) if task.image_ids else 0,
                annotations_count=annotations_count,
                reviewed_count=reviewed_count,
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
        logger.error(f"Failed to list annotation tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/annotation/tasks/{task_id}")
async def get_annotation_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> AnnotationTaskResponse:
    """
    获取标注任务详情

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.id == task_id,
            AnnotationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Annotation task not found")

    return AnnotationTaskResponse.model_validate(task)


@router.delete("/projects/{project_id}/annotation/tasks/{task_id}", status_code=204)
async def delete_annotation_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除标注任务

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    """
    task = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.id == task_id,
            AnnotationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Annotation task not found")

    # 只能删除已完成或失败的任务
    if task.status in ["processing", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete task in progress",
        )

    try:
        # 删除关联的标注记录
        db.query(Annotation).filter(Annotation.annotation_task_id == task_id).delete()

        db.delete(task)
        db.commit()

        logger.info(f"Deleted annotation task {task_id}")

    except Exception as e:
        logger.error(f"Failed to delete annotation task: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/annotation/tasks/{task_id}/annotations")
async def list_task_annotations(
    project_id: int,
    task_id: int,
    review_status: Optional[str] = Query(None, description="审核状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[AnnotationResponse]:
    """
    列出任务的标注结果

    - **project_id**: 项目ID
    - **task_id**: 任务ID
    - **review_status**: 审核状态筛选 (pending, approved, rejected)
    """
    # 验证任务存在
    task = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.id == task_id,
            AnnotationTask.project_id == project_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Annotation task not found")

    try:
        query = db.query(Annotation).filter(Annotation.annotation_task_id == task_id)

        # 审核状态筛选
        if review_status:
            query = query.filter(Annotation.review_status == review_status)

        # 总数
        total = query.count()

        # 分页查询
        annotations = (
            query.order_by(Annotation.image_id)
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [AnnotationResponse.model_validate(ann) for ann in annotations]

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except Exception as e:
        logger.error(f"Failed to list annotations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/images/{image_id}/annotations")
async def list_image_annotations(
    project_id: int,
    image_id: int,
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[AnnotationResponse]:
    """
    列出某张图片的所有标注

    - **project_id**: 项目ID
    - **image_id**: 图片ID
    """
    # 验证图片存在
    image = (
        db.query(ImageModel)
        .filter(
            ImageModel.id == image_id,
            ImageModel.project_id == project_id,
        )
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        query = db.query(Annotation).filter(Annotation.image_id == image_id)

        # 总数
        total = query.count()

        # 分页查询
        annotations = (
            query.order_by(Annotation.created_at)
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [AnnotationResponse.model_validate(ann) for ann in annotations]

        return PagedResponse(
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=(total + pagination["per_page"] - 1) // pagination["per_page"],
            items=items,
        )

    except Exception as e:
        logger.error(f"Failed to list image annotations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/annotations/{annotation_id}")
async def get_annotation(
    project_id: int,
    annotation_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> AnnotationResponse:
    """
    获取标注详情

    - **project_id**: 项目ID
    - **annotation_id**: 标注ID
    """
    annotation = (
        db.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Annotation.project_id == project_id,
        )
        .first()
    )

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    return AnnotationResponse.model_validate(annotation)


@router.patch("/projects/{project_id}/annotations/{annotation_id}/review")
async def review_annotation(
    project_id: int,
    annotation_id: int,
    review_data: AnnotationReviewRequest,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> AnnotationResponse:
    """
    审核标注

    - **project_id**: 项目ID
    - **annotation_id**: 标注ID
    - **review_data**: 审核数据
    """
    annotation = (
        db.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Annotation.project_id == project_id,
        )
        .first()
    )

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    try:
        # 更新审核状态
        annotation.review_status = review_data.review_status
        if review_data.review_notes:
            annotation.review_notes = review_data.review_notes

        # 如果提供了修正的边界框，更新标注
        if review_data.corrected_bbox:
            annotation.x_min = review_data.corrected_bbox.x_min
            annotation.y_min = review_data.corrected_bbox.y_min
            annotation.x_max = review_data.corrected_bbox.x_max
            annotation.y_max = review_data.corrected_bbox.y_max

        db.commit()
        db.refresh(annotation)

        logger.info(f"Annotation {annotation_id} reviewed: {review_data.review_status}")

        return AnnotationResponse.model_validate(annotation)

    except Exception as e:
        logger.error(f"Failed to review annotation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/annotations/{annotation_id}", status_code=204)
async def delete_annotation(
    project_id: int,
    annotation_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除标注

    - **project_id**: 项目ID
    - **annotation_id**: 标注ID
    """
    annotation = (
        db.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Annotation.project_id == project_id,
        )
        .first()
    )

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    try:
        db.delete(annotation)
        db.commit()

        logger.info(f"Deleted annotation {annotation_id}")

    except Exception as e:
        logger.error(f"Failed to delete annotation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/annotations/batch-delete", status_code=204)
async def batch_delete_annotations(
    project_id: int,
    annotation_ids: List[int],
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    批量删除标注

    - **project_id**: 项目ID
    - **annotation_ids**: 标注ID列表
    """
    # 验证标注存在
    annotations = (
        db.query(Annotation)
        .filter(
            Annotation.id.in_(annotation_ids),
            Annotation.project_id == project_id,
        )
        .all()
    )

    if len(annotations) != len(annotation_ids):
        raise HTTPException(
            status_code=404,
            detail="Some annotations not found or don't belong to this project",
        )

    try:
        # 批量删除
        db.query(Annotation).filter(Annotation.id.in_(annotation_ids)).delete(
            synchronize_session=False
        )
        db.commit()

        logger.info(f"Batch deleted {len(annotations)} annotations from project {project_id}")

    except Exception as e:
        logger.error(f"Failed to batch delete annotations: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/annotations/batch-by-label", status_code=204)
async def batch_delete_by_label(
    project_id: int,
    label_id: int = Query(..., description="要删除的标签ID"),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    批量删除指定标签的所有标注

    - **project_id**: 项目ID
    - **label_id**: 标签ID
    """
    try:
        # 删除指定标签的所有标注
        count = (
            db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.label_id == label_id,
            )
            .delete(synchronize_session=False)
        )

        db.commit()

        logger.info(f"Deleted {count} annotations with label {label_id} from project {project_id}")

        return {"deleted": count}

    except Exception as e:
        logger.error(f"Failed to batch delete by label: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/annotations/statistics")
async def get_annotation_statistics(
    project_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> dict:
    """
    获取标注统计信息

    - **project_id**: 项目ID
    """
    try:
        # 总标注数
        total = db.query(Annotation).filter(Annotation.project_id == project_id).count()

        # 按审核状态统计
        pending = (
            db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.review_status == "pending",
            )
            .count()
        )

        approved = (
            db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.review_status == "approved",
            )
            .count()
        )

        rejected = (
            db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.review_status == "rejected",
            )
            .count()
        )

        # 按标签统计
        from sqlalchemy import func
        from backend.models.project import Label

        label_stats = (
            db.query(
                Label.id,
                Label.name,
                func.count(Annotation.id).label("count"),
            )
            .join(Annotation, Annotation.label_id == Label.id)
            .filter(Annotation.project_id == project_id)
            .group_by(Label.id, Label.name)
            .all()
        )

        labels_count = {stat.name: stat.count for stat in label_stats}

        # 标注的图片数量
        annotated_images = (
            db.query(Annotation.image_id)
            .filter(Annotation.project_id == project_id)
            .distinct()
            .count()
        )

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "labels_count": labels_count,
            "annotated_images": annotated_images,
        }

    except Exception as e:
        logger.error(f"Failed to get annotation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: Annotation task execution has been moved to backend/tasks/annotation.py
# using Celery for better scalability and reliability
