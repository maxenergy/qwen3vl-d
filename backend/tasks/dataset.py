"""
数据集相关的Celery任务
Dataset Celery Tasks
"""

import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from celery import Task

from backend.celery_app import celery_app
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.core.logging import logger
from backend.models.dataset import DatasetVersion
from backend.models.annotation import Annotation
from backend.models.generation import Image as ImageModel
from backend.models.project import Label
from backend.services.dataset_converter import (
    YOLODatasetConverter,
    COCODatasetConverter,
    DatasetSplitter,
)


class DatabaseTask(Task):
    """带数据库会话的任务基类"""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """任务完成后关闭数据库连接"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.dataset.generate_dataset_task")
def generate_dataset_task(self, dataset_id: int):
    """
    生成数据集任务

    Args:
        dataset_id: 数据集版本ID
    """
    dataset = self.db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        logger.error(f"Dataset version {dataset_id} not found")
        return {"status": "error", "message": "Dataset not found"}

    try:
        # 更新状态为处理中
        dataset.status = "processing"
        self.db.commit()

        logger.info(f"Starting dataset generation {dataset_id}")

        # 获取项目标签
        labels = (
            self.db.query(Label)
            .filter(Label.project_id == dataset.project_id)
            .all()
        )

        # 如果指定了label_ids，筛选标签
        if dataset.label_ids:
            labels = [l for l in labels if l.id in dataset.label_ids]

        if not labels:
            raise ValueError("No labels found for dataset")

        # 创建标签映射（标签ID -> 类别索引）
        label_mapping = {label.id: idx for idx, label in enumerate(labels)}
        class_names = [label.name for label in labels]

        # 获取标注数据
        query = (
            self.db.query(Annotation)
            .filter(Annotation.project_id == dataset.project_id)
        )

        # 筛选条件
        filter_config = dataset.filter_config or {}

        if filter_config.get("approved_only", True):
            query = query.filter(Annotation.review_status == "approved")

        if filter_config.get("min_confidence"):
            query = query.filter(Annotation.confidence >= filter_config["min_confidence"])

        # 如果指定了标签，只获取这些标签的标注
        if dataset.label_ids:
            query = query.filter(Annotation.label_id.in_(dataset.label_ids))

        annotations = query.all()

        if not annotations:
            raise ValueError("No annotations found matching filter criteria")

        logger.info(f"Found {len(annotations)} annotations for dataset")

        # 获取唯一的图片ID
        image_ids = list(set(ann.image_id for ann in annotations))

        # 获取图片信息
        images = (
            self.db.query(ImageModel)
            .filter(ImageModel.id.in_(image_ids))
            .all()
        )

        # 转换为字典列表
        images_data = [
            {
                "id": img.id,
                "file_path": img.file_path,
                "width": img.width,
                "height": img.height,
            }
            for img in images
        ]

        annotations_data = [
            {
                "image_id": ann.image_id,
                "label_id": ann.label_id,
                "x_min": ann.x_min,
                "y_min": ann.y_min,
                "x_max": ann.x_max,
                "y_max": ann.y_max,
                "confidence": ann.confidence,
            }
            for ann in annotations
        ]

        # 数据集划分
        split_config = dataset.split_config or {}
        split_method = split_config.get("method", "ratio")

        if split_method == "ratio":
            train_images, val_images, test_images = DatasetSplitter.split_by_ratio(
                images_data,
                train_ratio=split_config.get("train_ratio", 0.8),
                val_ratio=split_config.get("val_ratio", 0.1),
                test_ratio=split_config.get("test_ratio", 0.1),
                shuffle=split_config.get("shuffle", True),
                seed=split_config.get("seed"),
            )
        elif split_method == "k_fold":
            # K折交叉验证只生成第一折作为示例
            k = split_config.get("k_folds", 5)
            folds = DatasetSplitter.k_fold_split(
                images_data,
                k=k,
                shuffle=split_config.get("shuffle", True),
                seed=split_config.get("seed"),
            )
            train_images, val_images = folds[0]
            test_images = []  # K折一般不需要测试集
        else:
            raise ValueError(f"Unknown split method: {split_method}")

        # 创建输出目录
        output_dir = os.path.join(
            str(settings.data_dir),
            "datasets",
            str(dataset.project_id),
            f"dataset_{dataset_id}",
        )
        os.makedirs(output_dir, exist_ok=True)

        # 根据格式转换数据集
        if dataset.format == "yolo":
            converter = YOLODatasetConverter(output_dir)

            # 转换各个分割
            stats = {}
            for split_name, split_images in [
                ("train", train_images),
                ("val", val_images),
                ("test", test_images),
            ]:
                if not split_images:
                    continue

                # 获取该分割的标注
                split_image_ids = [img["id"] for img in split_images]
                split_annotations = [
                    ann for ann in annotations_data if ann["image_id"] in split_image_ids
                ]

                result = converter.convert_annotations(
                    images=split_images,
                    annotations=split_annotations,
                    label_mapping=label_mapping,
                    split=split_name,
                )
                stats[split_name] = result

            # 创建data.yaml
            yaml_path = converter.create_data_yaml(
                class_names=class_names,
                dataset_name=dataset.name,
                description=dataset.description or "",
            )

        elif dataset.format == "coco":
            converter = COCODatasetConverter(output_dir)

            # COCO格式的categories
            categories = [
                {
                    "id": label.id,
                    "name": label.name,
                    "supercategory": "object",
                }
                for label in labels
            ]

            stats = {}
            for split_name, split_images in [
                ("train", train_images),
                ("val", val_images),
                ("test", test_images),
            ]:
                if not split_images:
                    continue

                split_image_ids = [img["id"] for img in split_images]
                split_annotations = [
                    ann for ann in annotations_data if ann["image_id"] in split_image_ids
                ]

                result = converter.convert_annotations(
                    images=split_images,
                    annotations=split_annotations,
                    categories=categories,
                    split=split_name,
                    dataset_info={
                        "description": dataset.description or "",
                        "version": dataset.version,
                        "year": datetime.now().year,
                    },
                )
                stats[split_name] = result

        else:
            raise ValueError(f"Unsupported format: {dataset.format}")

        # 更新数据集信息
        dataset.output_path = output_dir
        dataset.status = "completed"
        dataset.statistics = {
            "total_images": len(images_data),
            "total_annotations": len(annotations_data),
            "num_classes": len(class_names),
            "class_names": class_names,
            "splits": stats,
            "label_distribution": self._calculate_label_distribution(annotations_data, labels),
        }
        dataset.generated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Dataset generation {dataset_id} completed at {output_dir}")

        return {
            "status": "completed",
            "dataset_id": dataset_id,
            "output_path": output_dir,
            "statistics": dataset.statistics,
        }

    except Exception as e:
        logger.error(f"Dataset generation {dataset_id} failed: {e}")
        dataset.status = "failed"
        dataset.error_message = str(e)
        self.db.commit()

        return {
            "status": "failed",
            "dataset_id": dataset_id,
            "error": str(e),
        }

    def _calculate_label_distribution(
        self,
        annotations: List[Dict[str, Any]],
        labels: List[Label],
    ) -> Dict[str, int]:
        """计算标签分布"""
        distribution = {}
        label_id_to_name = {label.id: label.name for label in labels}

        for ann in annotations:
            label_name = label_id_to_name.get(ann["label_id"], "Unknown")
            distribution[label_name] = distribution.get(label_name, 0) + 1

        return distribution


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.dataset.export_dataset_task")
def export_dataset_task(
    self,
    dataset_id: int,
    format: str = "zip",
    include_images: bool = True,
    compress: bool = True,
):
    """
    导出数据集任务

    Args:
        dataset_id: 数据集ID
        format: 导出格式 (zip/tar)
        include_images: 是否包含图片
        compress: 是否压缩
    """
    dataset = self.db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        logger.error(f"Dataset {dataset_id} not found")
        return {"status": "error", "message": "Dataset not found"}

    if dataset.status != "completed":
        logger.error(f"Dataset {dataset_id} is not completed")
        return {"status": "error", "message": "Dataset not completed"}

    try:
        logger.info(f"Exporting dataset {dataset_id}")

        source_dir = Path(dataset.output_path)
        if not source_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {source_dir}")

        # 创建导出目录
        export_dir = source_dir.parent / "exports"
        export_dir.mkdir(exist_ok=True)

        # 导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{dataset.name}_v{dataset.version}_{timestamp}"

        if not include_images:
            # 只导出标注文件
            export_path = export_dir / f"{export_filename}_labels_only.zip"

            with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 添加标注文件
                if dataset.format == "yolo":
                    # 添加labels目录
                    labels_dir = source_dir / "labels"
                    for file_path in labels_dir.rglob("*.txt"):
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)

                    # 添加data.yaml
                    yaml_file = source_dir / "data.yaml"
                    if yaml_file.exists():
                        zipf.write(yaml_file, "data.yaml")

                elif dataset.format == "coco":
                    # 添加annotations目录
                    annotations_dir = source_dir / "annotations"
                    for file_path in annotations_dir.glob("*.json"):
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)

        else:
            # 完整导出
            if compress:
                export_path = export_dir / f"{export_filename}.zip"

                with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in source_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_dir)
                            zipf.write(file_path, arcname)
            else:
                # 复制整个目录
                export_path = export_dir / export_filename
                shutil.copytree(source_dir, export_path, dirs_exist_ok=True)

        logger.info(f"Dataset exported to {export_path}")

        return {
            "status": "completed",
            "dataset_id": dataset_id,
            "export_path": str(export_path),
            "size_bytes": os.path.getsize(export_path) if export_path.is_file() else 0,
        }

    except Exception as e:
        logger.error(f"Dataset export failed: {e}")
        return {
            "status": "failed",
            "dataset_id": dataset_id,
            "error": str(e),
        }


@celery_app.task(name="backend.tasks.dataset.cleanup_old_datasets")
def cleanup_old_datasets(days: int = 30):
    """
    清理旧的数据集文件

    Args:
        days: 清理多少天之前的数据集
    """
    db = SessionLocal()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 查找旧数据集
        old_datasets = (
            db.query(DatasetVersion)
            .filter(
                DatasetVersion.status == "completed",
                DatasetVersion.generated_at < cutoff_date,
            )
            .all()
        )

        cleaned = 0
        for dataset in old_datasets:
            try:
                if dataset.output_path and os.path.exists(dataset.output_path):
                    shutil.rmtree(dataset.output_path)
                    logger.info(f"Cleaned up dataset {dataset.id} at {dataset.output_path}")
                    cleaned += 1
            except Exception as e:
                logger.error(f"Failed to cleanup dataset {dataset.id}: {e}")

        logger.info(f"Cleaned up {cleaned} old datasets (older than {days} days)")

        return {
            "status": "success",
            "cleaned": cleaned,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old datasets: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()
