"""
数据集API路由
Dataset API Routes

数据集版本管理、格式转换和导出
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.api.dependencies import (
    get_db_session,
    get_project_or_404,
    get_pagination_params,
)
from backend.core.logging import logger
from backend.models.project import Project, Label
from backend.models.dataset import DatasetVersion
from backend.models.annotation import Annotation
from backend.models.generation import Image as ImageModel
from backend.schemas.dataset import (
    DatasetVersionCreate,
    DatasetVersionResponse,
    DatasetVersionListItem,
    DatasetExportRequest,
    DatasetExportResponse,
)
from backend.schemas.common import PagedResponse


router = APIRouter()


@router.post("/projects/{project_id}/datasets", status_code=201)
async def create_dataset_version(
    project_id: int,
    dataset_data: DatasetVersionCreate,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> DatasetVersionResponse:
    """
    创建数据集版本

    - **project_id**: 项目ID
    - **dataset_data**: 数据集配置
    """
    try:
        # 验证标签存在
        if dataset_data.label_ids:
            labels_count = (
                db.query(Label)
                .filter(
                    Label.id.in_(dataset_data.label_ids),
                    Label.project_id == project_id,
                    Label.is_active == True,
                )
                .count()
            )

            if labels_count != len(dataset_data.label_ids):
                raise HTTPException(
                    status_code=404,
                    detail="Some labels not found or are inactive",
                )

        # 创建数据集版本
        dataset = DatasetVersion(
            project_id=project_id,
            name=dataset_data.name,
            description=dataset_data.description,
            version=dataset_data.version,
            format=dataset_data.format,
            split_config={
                "method": dataset_data.split_method,
                "train_ratio": dataset_data.train_ratio,
                "val_ratio": dataset_data.val_ratio,
                "test_ratio": dataset_data.test_ratio,
                "k_folds": dataset_data.k_folds,
                "shuffle": dataset_data.shuffle,
                "seed": dataset_data.seed,
            },
            augmentation_config=dataset_data.augmentation_config,
            label_ids=dataset_data.label_ids,
            filter_config={
                "approved_only": dataset_data.approved_only,
                "min_confidence": dataset_data.min_confidence,
            },
            status="pending",
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        logger.info(f"Created dataset version {dataset.id} for project {project_id}")

        # 异步生成数据集
        from backend.tasks.dataset import generate_dataset_task
        generate_dataset_task.delay(dataset.id)

        return DatasetVersionResponse.model_validate(dataset)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dataset version: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")


@router.get("/projects/{project_id}/datasets")
async def list_dataset_versions(
    project_id: int,
    format: Optional[str] = Query(None, description="格式筛选 (yolo/coco)"),
    status: Optional[str] = Query(None, description="状态筛选"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> PagedResponse[DatasetVersionListItem]:
    """
    列出项目的数据集版本

    - **project_id**: 项目ID
    - **format**: 格式筛选 (yolo/coco)
    - **status**: 状态筛选 (pending/processing/completed/failed)
    """
    try:
        query = db.query(DatasetVersion).filter(DatasetVersion.project_id == project_id)

        # 格式筛选
        if format:
            query = query.filter(DatasetVersion.format == format)

        # 状态筛选
        if status:
            query = query.filter(DatasetVersion.status == status)

        # 总数
        total = query.count()

        # 分页查询
        datasets = (
            query.order_by(desc(DatasetVersion.created_at))
            .offset(pagination["skip"])
            .limit(pagination["per_page"])
            .all()
        )

        items = [DatasetVersionListItem.model_validate(ds) for ds in datasets]

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
        logger.error(f"Failed to list dataset versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/datasets/{dataset_id}")
async def get_dataset_version(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> DatasetVersionResponse:
    """
    获取数据集版本详情

    - **project_id**: 项目ID
    - **dataset_id**: 数据集ID
    """
    dataset = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_id,
            DatasetVersion.project_id == project_id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found")

    return DatasetVersionResponse.model_validate(dataset)


@router.delete("/projects/{project_id}/datasets/{dataset_id}", status_code=204)
async def delete_dataset_version(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
):
    """
    删除数据集版本

    - **project_id**: 项目ID
    - **dataset_id**: 数据集ID
    """
    dataset = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_id,
            DatasetVersion.project_id == project_id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found")

    try:
        # 删除数据集文件
        import shutil
        if dataset.output_path and os.path.exists(dataset.output_path):
            shutil.rmtree(dataset.output_path)
            logger.info(f"Deleted dataset files at {dataset.output_path}")

        db.delete(dataset)
        db.commit()

        logger.info(f"Deleted dataset version {dataset_id}")

    except Exception as e:
        logger.error(f"Failed to delete dataset version: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/datasets/{dataset_id}/export")
async def export_dataset(
    project_id: int,
    dataset_id: int,
    export_request: DatasetExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> DatasetExportResponse:
    """
    导出数据集

    - **project_id**: 项目ID
    - **dataset_id**: 数据集ID
    - **export_request**: 导出配置
    """
    dataset = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_id,
            DatasetVersion.project_id == project_id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found")

    if dataset.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Dataset status is {dataset.status}, must be completed to export",
        )

    try:
        # 创建导出任务
        from backend.tasks.dataset import export_dataset_task

        task_result = export_dataset_task.delay(
            dataset_id=dataset_id,
            format=export_request.format,
            include_images=export_request.include_images,
            compress=export_request.compress,
        )

        return DatasetExportResponse(
            dataset_id=dataset_id,
            task_id=task_result.id,
            status="processing",
            message="Export task started",
        )

    except Exception as e:
        logger.error(f"Failed to start export task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/datasets/{dataset_id}/regenerate")
async def regenerate_dataset(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> DatasetVersionResponse:
    """
    重新生成数据集

    - **project_id**: 项目ID
    - **dataset_id**: 数据集ID
    """
    dataset = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_id,
            DatasetVersion.project_id == project_id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found")

    try:
        # 重置状态
        dataset.status = "pending"
        dataset.error_message = None
        dataset.statistics = None

        db.commit()
        db.refresh(dataset)

        # 重新生成
        from backend.tasks.dataset import generate_dataset_task
        generate_dataset_task.delay(dataset.id)

        logger.info(f"Regenerating dataset {dataset_id}")

        return DatasetVersionResponse.model_validate(dataset)

    except Exception as e:
        logger.error(f"Failed to regenerate dataset: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/datasets/{dataset_id}/statistics")
async def get_dataset_statistics(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> dict:
    """
    获取数据集统计信息

    - **project_id**: 项目ID
    - **dataset_id**: 数据集ID
    """
    dataset = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_id,
            DatasetVersion.project_id == project_id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found")

    # 返回存储的统计信息
    if dataset.statistics:
        return dataset.statistics

    # 如果没有统计信息，返回基本信息
    return {
        "status": dataset.status,
        "format": dataset.format,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
    }


@router.get("/projects/{project_id}/datasets/quick-stats")
async def get_quick_dataset_stats(
    project_id: int,
    db: Session = Depends(get_db_session),
    project: Project = Depends(get_project_or_404),
) -> dict:
    """
    获取项目数据集快速统计

    - **project_id**: 项目ID
    """
    try:
        # 统计已审核的标注数量
        approved_annotations = (
            db.query(Annotation)
            .filter(
                Annotation.project_id == project_id,
                Annotation.review_status == "approved",
            )
            .count()
        )

        # 统计已审核的图片数量
        approved_images = (
            db.query(Annotation.image_id)
            .filter(
                Annotation.project_id == project_id,
                Annotation.review_status == "approved",
            )
            .distinct()
            .count()
        )

        # 统计激活的标签数量
        active_labels = (
            db.query(Label)
            .filter(
                Label.project_id == project_id,
                Label.is_active == True,
            )
            .count()
        )

        # 统计数据集版本
        dataset_versions = (
            db.query(DatasetVersion)
            .filter(DatasetVersion.project_id == project_id)
            .count()
        )

        completed_datasets = (
            db.query(DatasetVersion)
            .filter(
                DatasetVersion.project_id == project_id,
                DatasetVersion.status == "completed",
            )
            .count()
        )

        return {
            "approved_annotations": approved_annotations,
            "approved_images": approved_images,
            "active_labels": active_labels,
            "dataset_versions": dataset_versions,
            "completed_datasets": completed_datasets,
            "ready_for_training": approved_images > 0 and active_labels > 0,
        }

    except Exception as e:
        logger.error(f"Failed to get quick stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import os
# Note: Dataset generation logic has been moved to backend/tasks/dataset.py
# using Celery for better scalability and reliability
