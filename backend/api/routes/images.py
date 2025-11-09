"""
图片管理与审核API路由
Image Management and Review API Routes
"""

from typing import Optional, List

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
from backend.models.generation import Image as ImageModel
from backend.schemas.generation import (
    ImageResponse,
    ImageReviewRequest,
    BatchImageReviewRequest,
)
from backend.schemas.common import PagedResponse


router = APIRouter()


@router.get("/projects/{project_id}/images")
async def list_project_images(
    project_id: int,
    review_status: Optional[str] = Query(None, description="审核状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[ImageResponse]:
    """
    列出项目的所有图片

    - **project_id**: 项目ID
    - **review_status**: 审核状态筛选 (pending, approved, rejected)
    - **page**: 页码
    - **per_page**: 每页数量
    """
    try:
        query = db.query(ImageModel).filter(ImageModel.project_id == project_id)

        # 审核状态筛选
        if review_status:
            query = query.filter(ImageModel.review_status == review_status)

        # 总数
        total = query.count()

        # 分页查询
        images = (
            query.order_by(desc(ImageModel.created_at))
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
        logger.error(f"Failed to list project images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/images/{image_id}")
async def get_image(
    project_id: int,
    image_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> ImageResponse:
    """
    获取图片详情

    - **project_id**: 项目ID
    - **image_id**: 图片ID
    """
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

    return ImageResponse.model_validate(image)


@router.patch("/projects/{project_id}/images/{image_id}/review")
async def review_image(
    project_id: int,
    image_id: int,
    review_data: ImageReviewRequest,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> ImageResponse:
    """
    审核图片

    - **project_id**: 项目ID
    - **image_id**: 图片ID
    - **review_data**: 审核数据（状态和备注）
    """
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
        # 更新审核状态
        image.review_status = review_data.review_status
        if review_data.review_notes:
            image.review_notes = review_data.review_notes

        db.commit()
        db.refresh(image)

        logger.info(f"Image {image_id} reviewed: {review_data.review_status}")

        return ImageResponse.model_validate(image)

    except Exception as e:
        logger.error(f"Failed to review image: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/images/review/batch")
async def batch_review_images(
    project_id: int,
    review_data: BatchImageReviewRequest,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> dict:
    """
    批量审核图片

    - **project_id**: 项目ID
    - **review_data**: 批量审核数据
    """
    try:
        # 验证图片存在且属于该项目
        images = (
            db.query(ImageModel)
            .filter(
                ImageModel.id.in_(review_data.image_ids),
                ImageModel.project_id == project_id,
            )
            .all()
        )

        if len(images) != len(review_data.image_ids):
            raise HTTPException(
                status_code=404,
                detail="Some images not found or don't belong to this project",
            )

        # 批量更新
        for image in images:
            image.review_status = review_data.review_status
            if review_data.review_notes:
                image.review_notes = review_data.review_notes

        db.commit()

        logger.info(
            f"Batch reviewed {len(images)} images in project {project_id}: {review_data.review_status}"
        )

        return {
            "updated": len(images),
            "review_status": review_data.review_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch review images: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/images/{image_id}", status_code=204)
async def delete_image(
    project_id: int,
    image_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除图片

    - **project_id**: 项目ID
    - **image_id**: 图片ID
    """
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
        # 删除文件
        import os
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
            logger.info(f"Deleted image file: {image.file_path}")

        # 删除数据库记录
        db.delete(image)
        db.commit()

        logger.info(f"Deleted image {image_id}")

    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/images/delete/batch", status_code=204)
async def batch_delete_images(
    project_id: int,
    image_ids: List[int],
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    批量删除图片

    - **project_id**: 项目ID
    - **image_ids**: 图片ID列表
    """
    # 验证图片存在且属于该项目
    images = (
        db.query(ImageModel)
        .filter(
            ImageModel.id.in_(image_ids),
            ImageModel.project_id == project_id,
        )
        .all()
    )

    if len(images) != len(image_ids):
        raise HTTPException(
            status_code=404,
            detail="Some images not found or don't belong to this project",
        )

    try:
        import os

        # 删除文件
        for image in images:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)

        # 批量删除记录
        db.query(ImageModel).filter(ImageModel.id.in_(image_ids)).delete(
            synchronize_session=False
        )
        db.commit()

        logger.info(f"Batch deleted {len(images)} images from project {project_id}")

    except Exception as e:
        logger.error(f"Failed to batch delete images: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/images/statistics")
async def get_image_statistics(
    project_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> dict:
    """
    获取图片统计信息

    - **project_id**: 项目ID
    """
    try:
        # 总图片数
        total = db.query(ImageModel).filter(ImageModel.project_id == project_id).count()

        # 按审核状态统计
        pending = (
            db.query(ImageModel)
            .filter(
                ImageModel.project_id == project_id,
                ImageModel.review_status == "pending",
            )
            .count()
        )

        approved = (
            db.query(ImageModel)
            .filter(
                ImageModel.project_id == project_id,
                ImageModel.review_status == "approved",
            )
            .count()
        )

        rejected = (
            db.query(ImageModel)
            .filter(
                ImageModel.project_id == project_id,
                ImageModel.review_status == "rejected",
            )
            .count()
        )

        # 计算总文件大小
        from sqlalchemy import func

        total_size = (
            db.query(func.sum(ImageModel.file_size))
            .filter(ImageModel.project_id == project_id)
            .scalar()
        ) or 0

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    except Exception as e:
        logger.error(f"Failed to get image statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
