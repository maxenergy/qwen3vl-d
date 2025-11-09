"""
数据集格式转换服务
Dataset Format Conversion Service

支持YOLO和COCO格式的数据集导出
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from PIL import Image

from backend.core.config import settings
from backend.core.logging import logger


class YOLODatasetConverter:
    """YOLO格式数据集转换器"""

    def __init__(self, output_dir: str):
        """
        初始化YOLO转换器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.labels_dir = self.output_dir / "labels"

        # 创建目录结构
        for split in ["train", "val", "test"]:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)

    def convert_annotations(
        self,
        images: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]],
        label_mapping: Dict[int, int],  # {label_id: class_index}
        split: str = "train",
    ) -> Dict[str, Any]:
        """
        转换标注为YOLO格式

        Args:
            images: 图片列表 [{id, file_path, width, height}, ...]
            annotations: 标注列表 [{image_id, label_id, x_min, y_min, x_max, y_max}, ...]
            label_mapping: 标签ID到类别索引的映射
            split: 数据集分割 (train/val/test)

        Returns:
            转换结果统计
        """
        logger.info(f"Converting {len(images)} images to YOLO format ({split})")

        # 按图片组织标注
        image_annotations = {}
        for ann in annotations:
            image_id = ann["image_id"]
            if image_id not in image_annotations:
                image_annotations[image_id] = []
            image_annotations[image_id].append(ann)

        converted_images = 0
        converted_annotations = 0
        skipped = 0

        for image_info in images:
            try:
                image_id = image_info["id"]
                source_path = image_info["file_path"]

                if not os.path.exists(source_path):
                    logger.warning(f"Image not found: {source_path}")
                    skipped += 1
                    continue

                # 复制图片
                image_filename = f"{image_id}_{Path(source_path).name}"
                dest_image_path = self.images_dir / split / image_filename
                shutil.copy2(source_path, dest_image_path)

                # 生成YOLO标注文件
                label_filename = Path(image_filename).stem + ".txt"
                label_path = self.labels_dir / split / label_filename

                # 获取该图片的所有标注
                img_anns = image_annotations.get(image_id, [])

                with open(label_path, "w") as f:
                    for ann in img_anns:
                        # 获取类别索引
                        class_idx = label_mapping.get(ann["label_id"])
                        if class_idx is None:
                            logger.warning(f"Label {ann['label_id']} not in mapping")
                            continue

                        # 归一化坐标已经是0-1，直接使用
                        x_min = ann["x_min"]
                        y_min = ann["y_min"]
                        x_max = ann["x_max"]
                        y_max = ann["y_max"]

                        # 转换为YOLO格式 (center_x, center_y, width, height)
                        center_x = (x_min + x_max) / 2.0
                        center_y = (y_min + y_max) / 2.0
                        width = x_max - x_min
                        height = y_max - y_min

                        # 写入YOLO格式: class_idx center_x center_y width height
                        f.write(f"{class_idx} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                        converted_annotations += 1

                converted_images += 1

            except Exception as e:
                logger.error(f"Failed to convert image {image_info.get('id')}: {e}")
                skipped += 1

        logger.info(
            f"YOLO conversion complete: {converted_images} images, "
            f"{converted_annotations} annotations, {skipped} skipped"
        )

        return {
            "split": split,
            "converted_images": converted_images,
            "converted_annotations": converted_annotations,
            "skipped": skipped,
        }

    def create_data_yaml(
        self,
        class_names: List[str],
        dataset_name: str = "dataset",
        description: str = "",
    ) -> str:
        """
        创建YOLO数据集配置文件 (data.yaml)

        Args:
            class_names: 类别名称列表（按索引顺序）
            dataset_name: 数据集名称
            description: 数据集描述

        Returns:
            配置文件路径
        """
        yaml_path = self.output_dir / "data.yaml"

        # 相对路径
        config = {
            "path": str(self.output_dir.absolute()),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "nc": len(class_names),  # number of classes
            "names": class_names,
        }

        # 添加元数据
        if dataset_name:
            config["dataset_name"] = dataset_name
        if description:
            config["description"] = description

        # 写入YAML文件
        import yaml

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info(f"Created data.yaml at {yaml_path}")
        return str(yaml_path)


class COCODatasetConverter:
    """COCO格式数据集转换器"""

    def __init__(self, output_dir: str):
        """
        初始化COCO转换器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.annotations_dir = self.output_dir / "annotations"

        # 创建目录
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)

    def convert_annotations(
        self,
        images: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],  # [{id, name, supercategory}, ...]
        split: str = "train",
        dataset_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        转换标注为COCO格式

        Args:
            images: 图片列表
            annotations: 标注列表
            categories: 类别列表
            split: 数据集分割
            dataset_info: 数据集元信息

        Returns:
            转换结果统计
        """
        logger.info(f"Converting to COCO format ({split})")

        # COCO格式结构
        coco_data = {
            "info": dataset_info or self._default_info(),
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": categories,
        }

        # 复制图片并构建images列表
        converted_images = 0
        skipped = 0

        for img_info in images:
            try:
                source_path = img_info["file_path"]

                if not os.path.exists(source_path):
                    logger.warning(f"Image not found: {source_path}")
                    skipped += 1
                    continue

                # 复制图片到images目录
                image_filename = f"{img_info['id']}_{Path(source_path).name}"
                dest_path = self.images_dir / image_filename
                shutil.copy2(source_path, dest_path)

                # 添加到COCO images列表
                coco_data["images"].append({
                    "id": img_info["id"],
                    "file_name": image_filename,
                    "width": img_info["width"],
                    "height": img_info["height"],
                    "date_captured": datetime.utcnow().isoformat(),
                })

                converted_images += 1

            except Exception as e:
                logger.error(f"Failed to process image {img_info.get('id')}: {e}")
                skipped += 1

        # 转换标注
        converted_annotations = 0

        for idx, ann in enumerate(annotations, start=1):
            try:
                img_info = next((img for img in images if img["id"] == ann["image_id"]), None)
                if not img_info:
                    logger.warning(f"Image {ann['image_id']} not found for annotation")
                    continue

                # 归一化坐标转换为像素坐标
                x_min = ann["x_min"] * img_info["width"]
                y_min = ann["y_min"] * img_info["height"]
                x_max = ann["x_max"] * img_info["width"]
                y_max = ann["y_max"] * img_info["height"]

                # COCO格式: [x, y, width, height]
                width = x_max - x_min
                height = y_max - y_min
                area = width * height

                coco_data["annotations"].append({
                    "id": idx,
                    "image_id": ann["image_id"],
                    "category_id": ann["label_id"],
                    "bbox": [x_min, y_min, width, height],
                    "area": area,
                    "iscrowd": 0,
                    "segmentation": [],  # 暂不支持分割
                })

                converted_annotations += 1

            except Exception as e:
                logger.error(f"Failed to convert annotation: {e}")

        # 保存COCO JSON文件
        json_filename = f"instances_{split}.json"
        json_path = self.annotations_dir / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"COCO conversion complete: {converted_images} images, "
            f"{converted_annotations} annotations, saved to {json_path}"
        )

        return {
            "split": split,
            "converted_images": converted_images,
            "converted_annotations": converted_annotations,
            "skipped": skipped,
            "json_path": str(json_path),
        }

    def _default_info(self) -> Dict[str, Any]:
        """默认数据集信息"""
        return {
            "year": datetime.now().year,
            "version": "1.0",
            "description": "Auto-annotated dataset",
            "contributor": "Auto Annotation Tool",
            "url": "",
            "date_created": datetime.utcnow().isoformat(),
        }


class DatasetSplitter:
    """数据集划分器"""

    @staticmethod
    def split_by_ratio(
        items: List[Any],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        shuffle: bool = True,
        seed: Optional[int] = None,
    ) -> Tuple[List[Any], List[Any], List[Any]]:
        """
        按比例划分数据集

        Args:
            items: 数据项列表
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            shuffle: 是否打乱
            seed: 随机种子

        Returns:
            (train_items, val_items, test_items)
        """
        import random

        # 验证比例
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.001:
            raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")

        # 复制列表
        items_copy = items.copy()

        # 打乱
        if shuffle:
            if seed is not None:
                random.seed(seed)
            random.shuffle(items_copy)

        # 计算分割点
        total = len(items_copy)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        # 分割
        train_items = items_copy[:train_end]
        val_items = items_copy[train_end:val_end]
        test_items = items_copy[val_end:]

        logger.info(
            f"Split {total} items: train={len(train_items)}, "
            f"val={len(val_items)}, test={len(test_items)}"
        )

        return train_items, val_items, test_items

    @staticmethod
    def k_fold_split(
        items: List[Any],
        k: int = 5,
        shuffle: bool = True,
        seed: Optional[int] = None,
    ) -> List[Tuple[List[Any], List[Any]]]:
        """
        K折交叉验证划分

        Args:
            items: 数据项列表
            k: 折数
            shuffle: 是否打乱
            seed: 随机种子

        Returns:
            [(train_items, val_items), ...] 共k组
        """
        import random

        if k < 2:
            raise ValueError(f"k must be >= 2, got {k}")

        # 复制并打乱
        items_copy = items.copy()
        if shuffle:
            if seed is not None:
                random.seed(seed)
            random.shuffle(items_copy)

        # 计算每折大小
        total = len(items_copy)
        fold_size = total // k

        folds = []
        for i in range(k):
            # 验证集索引
            val_start = i * fold_size
            val_end = (i + 1) * fold_size if i < k - 1 else total

            # 分割
            val_items = items_copy[val_start:val_end]
            train_items = items_copy[:val_start] + items_copy[val_end:]

            folds.append((train_items, val_items))

            logger.debug(
                f"Fold {i+1}/{k}: train={len(train_items)}, val={len(val_items)}"
            )

        logger.info(f"Created {k}-fold split with {total} items")

        return folds


class DataAugmentationConfig:
    """数据增强配置"""

    def __init__(self):
        self.enabled = True
        self.augmentations = {
            # 几何变换
            "horizontal_flip": True,
            "vertical_flip": False,
            "rotate": {"enabled": True, "degrees": [-10, 10]},
            "scale": {"enabled": True, "range": [0.8, 1.2]},
            "translate": {"enabled": True, "range": [-0.1, 0.1]},
            "shear": {"enabled": False, "range": [-5, 5]},

            # 颜色变换
            "brightness": {"enabled": True, "range": [0.8, 1.2]},
            "contrast": {"enabled": True, "range": [0.8, 1.2]},
            "saturation": {"enabled": True, "range": [0.8, 1.2]},
            "hue": {"enabled": False, "range": [-0.1, 0.1]},

            # 噪声和模糊
            "gaussian_noise": {"enabled": False, "sigma": [0, 0.05]},
            "gaussian_blur": {"enabled": False, "kernel_size": [3, 7]},

            # Mosaic和Mixup
            "mosaic": {"enabled": False, "prob": 0.5},
            "mixup": {"enabled": False, "prob": 0.5, "alpha": 0.5},
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "augmentations": self.augmentations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataAugmentationConfig":
        """从字典创建"""
        config = cls()
        config.enabled = data.get("enabled", True)
        config.augmentations.update(data.get("augmentations", {}))
        return config

    def to_ultralytics_args(self) -> Dict[str, Any]:
        """
        转换为Ultralytics YOLO训练参数

        Returns:
            训练参数字典
        """
        args = {}

        if not self.enabled:
            # 禁用所有增强
            args.update({
                "hsv_h": 0.0,
                "hsv_s": 0.0,
                "hsv_v": 0.0,
                "degrees": 0.0,
                "translate": 0.0,
                "scale": 0.0,
                "shear": 0.0,
                "perspective": 0.0,
                "flipud": 0.0,
                "fliplr": 0.0,
                "mosaic": 0.0,
                "mixup": 0.0,
            })
            return args

        # 映射配置到YOLO参数
        aug = self.augmentations

        # 翻转
        if aug.get("horizontal_flip"):
            args["fliplr"] = 0.5
        if aug.get("vertical_flip"):
            args["flipud"] = 0.5

        # 旋转
        if aug.get("rotate", {}).get("enabled"):
            degrees_range = aug["rotate"].get("degrees", [-10, 10])
            args["degrees"] = abs(degrees_range[1] - degrees_range[0]) / 2

        # 缩放
        if aug.get("scale", {}).get("enabled"):
            scale_range = aug["scale"].get("range", [0.8, 1.2])
            args["scale"] = abs(scale_range[1] - scale_range[0])

        # 平移
        if aug.get("translate", {}).get("enabled"):
            translate_range = aug["translate"].get("range", [-0.1, 0.1])
            args["translate"] = abs(translate_range[1])

        # 剪切
        if aug.get("shear", {}).get("enabled"):
            shear_range = aug["shear"].get("range", [-5, 5])
            args["shear"] = abs(shear_range[1])

        # 颜色增强（HSV）
        if aug.get("hue", {}).get("enabled"):
            hue_range = aug["hue"].get("range", [-0.1, 0.1])
            args["hsv_h"] = abs(hue_range[1])

        if aug.get("saturation", {}).get("enabled"):
            sat_range = aug["saturation"].get("range", [0.8, 1.2])
            args["hsv_s"] = abs(sat_range[1] - 1.0)

        if aug.get("brightness", {}).get("enabled"):
            bright_range = aug["brightness"].get("range", [0.8, 1.2])
            args["hsv_v"] = abs(bright_range[1] - 1.0)

        # Mosaic
        if aug.get("mosaic", {}).get("enabled"):
            args["mosaic"] = aug["mosaic"].get("prob", 0.5)

        # Mixup
        if aug.get("mixup", {}).get("enabled"):
            args["mixup"] = aug["mixup"].get("prob", 0.5)

        return args


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("Dataset Conversion Service Test")
    print("=" * 60)

    # 测试数据集划分
    items = list(range(100))
    train, val, test = DatasetSplitter.split_by_ratio(items, 0.8, 0.1, 0.1)
    print(f"\nSplit test: train={len(train)}, val={len(val)}, test={len(test)}")

    # 测试K折划分
    folds = DatasetSplitter.k_fold_split(items, k=5)
    print(f"\nK-fold test: {len(folds)} folds created")

    # 测试数据增强配置
    aug_config = DataAugmentationConfig()
    yolo_args = aug_config.to_ultralytics_args()
    print(f"\nAugmentation config: {yolo_args}")

    print("=" * 60)
