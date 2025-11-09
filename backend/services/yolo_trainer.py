"""
YOLO训练服务
YOLO Training Service

使用Ultralytics YOLO进行模型训练
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ultralytics import YOLO

from backend.core.config import settings
from backend.core.logging import logger


class YOLOTrainer:
    """YOLO训练器"""

    # 支持的YOLO版本
    SUPPORTED_VERSIONS = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x",
                          "yolov11n", "yolov11s", "yolov11m", "yolov11l", "yolov11x"]

    # 预训练模型映射
    PRETRAINED_MODELS = {
        "yolov8n": "yolov8n.pt",
        "yolov8s": "yolov8s.pt",
        "yolov8m": "yolov8m.pt",
        "yolov8l": "yolov8l.pt",
        "yolov8x": "yolov8x.pt",
        "yolov11n": "yolo11n.pt",
        "yolov11s": "yolo11s.pt",
        "yolov11m": "yolo11m.pt",
        "yolov11l": "yolo11l.pt",
        "yolov11x": "yolo11x.pt",
    }

    def __init__(
        self,
        model_version: str = "yolov8n",
        pretrained: bool = True,
        device: Optional[str] = None,
    ):
        """
        初始化YOLO训练器

        Args:
            model_version: 模型版本 (yolov8n, yolov8s, ..., yolov11x)
            pretrained: 是否使用预训练权重
            device: 设备 (cuda:0, cpu等)
        """
        if model_version not in self.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported model version: {model_version}. "
                f"Supported: {self.SUPPORTED_VERSIONS}"
            )

        self.model_version = model_version
        self.pretrained = pretrained
        self.device = device or settings.default_device

        # 初始化模型
        self.model = self._load_model()

    def _load_model(self) -> YOLO:
        """加载YOLO模型"""
        try:
            if self.pretrained:
                # 使用预训练权重
                model_name = self.PRETRAINED_MODELS[self.model_version]
                logger.info(f"Loading pretrained model: {model_name}")
                model = YOLO(model_name)
            else:
                # 从配置文件创建
                config_name = f"{self.model_version}.yaml"
                logger.info(f"Creating model from config: {config_name}")
                model = YOLO(config_name)

            return model

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load YOLO model: {e}")

    def train(
        self,
        data_yaml: str,
        epochs: int = 100,
        batch_size: int = 16,
        imgsz: int = 640,
        project: Optional[str] = None,
        name: Optional[str] = None,
        save_dir: Optional[str] = None,
        resume: bool = False,
        optimizer: str = "auto",
        lr0: float = 0.01,
        lrf: float = 0.01,
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        warmup_epochs: float = 3.0,
        warmup_momentum: float = 0.8,
        warmup_bias_lr: float = 0.1,
        patience: int = 100,
        close_mosaic: int = 10,
        amp: bool = True,
        fraction: float = 1.0,
        profile: bool = False,
        freeze: Optional[int] = None,
        multi_scale: bool = False,
        augment_config: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        训练YOLO模型

        Args:
            data_yaml: 数据集配置文件路径
            epochs: 训练轮数
            batch_size: 批次大小
            imgsz: 图片尺寸
            project: 项目目录
            name: 实验名称
            save_dir: 保存目录
            resume: 是否恢复训练
            optimizer: 优化器 (SGD, Adam, AdamW, auto)
            lr0: 初始学习率
            lrf: 最终学习率 (lr0 * lrf)
            momentum: SGD动量或Adam beta1
            weight_decay: 权重衰减
            warmup_epochs: 预热轮数
            warmup_momentum: 预热动量
            warmup_bias_lr: 预热偏置学习率
            patience: EarlyStopping耐心值
            close_mosaic: 关闭mosaic增强的轮数
            amp: 自动混合精度训练
            fraction: 训练数据比例
            profile: 是否性能分析
            freeze: 冻结层数
            multi_scale: 多尺度训练
            augment_config: 数据增强配置
            callback: 回调函数
            **kwargs: 其他参数

        Returns:
            训练结果字典
        """
        try:
            # 验证数据集配置文件
            if not os.path.exists(data_yaml):
                raise FileNotFoundError(f"Data config not found: {data_yaml}")

            # 准备训练参数
            train_args = {
                "data": data_yaml,
                "epochs": epochs,
                "batch": batch_size,
                "imgsz": imgsz,
                "device": self.device,
                "optimizer": optimizer,
                "lr0": lr0,
                "lrf": lrf,
                "momentum": momentum,
                "weight_decay": weight_decay,
                "warmup_epochs": warmup_epochs,
                "warmup_momentum": warmup_momentum,
                "warmup_bias_lr": warmup_bias_lr,
                "patience": patience,
                "close_mosaic": close_mosaic,
                "amp": amp,
                "fraction": fraction,
                "profile": profile,
                "resume": resume,
            }

            # 保存目录
            if save_dir:
                train_args["project"] = save_dir
            elif project and name:
                train_args["project"] = project
                train_args["name"] = name

            # 冻结层
            if freeze is not None:
                train_args["freeze"] = freeze

            # 多尺度
            if multi_scale:
                train_args["multi_scale"] = True

            # 数据增强配置
            if augment_config:
                train_args.update(augment_config)

            # 其他参数
            train_args.update(kwargs)

            logger.info(f"Starting training with args: {train_args}")

            # 开始训练
            results = self.model.train(**train_args)

            logger.info("Training completed successfully")

            # 返回结果
            return self._parse_training_results(results)

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise RuntimeError(f"YOLO training failed: {e}")

    def _parse_training_results(self, results) -> Dict[str, Any]:
        """解析训练结果"""
        try:
            # 提取关键指标
            metrics = {}

            if hasattr(results, "results_dict"):
                metrics = results.results_dict
            elif hasattr(results, "maps"):
                metrics = {
                    "map50": float(results.maps[0]) if results.maps else 0.0,
                    "map50-95": float(results.maps[1]) if len(results.maps) > 1 else 0.0,
                }

            # 获取保存路径
            save_dir = getattr(results, "save_dir", None)

            # 最佳模型路径
            best_model = None
            if save_dir:
                best_path = Path(save_dir) / "weights" / "best.pt"
                if best_path.exists():
                    best_model = str(best_path)

            return {
                "status": "completed",
                "metrics": metrics,
                "save_dir": str(save_dir) if save_dir else None,
                "best_model": best_model,
            }

        except Exception as e:
            logger.error(f"Failed to parse training results: {e}")
            return {
                "status": "completed",
                "metrics": {},
                "save_dir": None,
                "best_model": None,
            }

    def validate(
        self,
        data_yaml: str,
        batch_size: int = 16,
        imgsz: int = 640,
        conf: float = 0.001,
        iou: float = 0.6,
        max_det: int = 300,
        split: str = "val",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        验证模型

        Args:
            data_yaml: 数据集配置文件
            batch_size: 批次大小
            imgsz: 图片尺寸
            conf: 置信度阈值
            iou: NMS IoU阈值
            max_det: 最大检测数
            split: 数据集分割 (val, test)
            **kwargs: 其他参数

        Returns:
            验证结果
        """
        try:
            val_args = {
                "data": data_yaml,
                "batch": batch_size,
                "imgsz": imgsz,
                "conf": conf,
                "iou": iou,
                "max_det": max_det,
                "split": split,
                "device": self.device,
            }
            val_args.update(kwargs)

            logger.info(f"Starting validation with args: {val_args}")

            results = self.model.val(**val_args)

            logger.info("Validation completed")

            return self._parse_validation_results(results)

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise RuntimeError(f"YOLO validation failed: {e}")

    def _parse_validation_results(self, results) -> Dict[str, Any]:
        """解析验证结果"""
        try:
            metrics = {}

            if hasattr(results, "results_dict"):
                metrics = results.results_dict
            else:
                # 提取关键指标
                if hasattr(results, "box"):
                    box = results.box
                    metrics = {
                        "precision": float(box.p) if hasattr(box, "p") else 0.0,
                        "recall": float(box.r) if hasattr(box, "r") else 0.0,
                        "map50": float(box.map50) if hasattr(box, "map50") else 0.0,
                        "map50-95": float(box.map) if hasattr(box, "map") else 0.0,
                    }

            return {
                "status": "completed",
                "metrics": metrics,
            }

        except Exception as e:
            logger.error(f"Failed to parse validation results: {e}")
            return {
                "status": "completed",
                "metrics": {},
            }

    def export(
        self,
        format: str = "onnx",
        imgsz: int = 640,
        optimize: bool = False,
        half: bool = False,
        int8: bool = False,
        dynamic: bool = False,
        simplify: bool = False,
        **kwargs,
    ) -> str:
        """
        导出模型

        Args:
            format: 导出格式 (onnx, torchscript, tflite, etc.)
            imgsz: 图片尺寸
            optimize: 优化模型
            half: FP16量化
            int8: INT8量化
            dynamic: 动态输入尺寸
            simplify: 简化ONNX
            **kwargs: 其他参数

        Returns:
            导出模型路径
        """
        try:
            export_args = {
                "format": format,
                "imgsz": imgsz,
                "optimize": optimize,
                "half": half,
                "int8": int8,
                "dynamic": dynamic,
                "simplify": simplify,
            }
            export_args.update(kwargs)

            logger.info(f"Exporting model with args: {export_args}")

            export_path = self.model.export(**export_args)

            logger.info(f"Model exported to {export_path}")

            return str(export_path)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise RuntimeError(f"YOLO export failed: {e}")

    def load_checkpoint(self, checkpoint_path: str):
        """
        加载检查点

        Args:
            checkpoint_path: 检查点文件路径
        """
        try:
            logger.info(f"Loading checkpoint from {checkpoint_path}")
            self.model = YOLO(checkpoint_path)
            logger.info("Checkpoint loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            raise RuntimeError(f"Failed to load checkpoint: {e}")

    @staticmethod
    def get_training_hyperparameters(
        preset: str = "default",
    ) -> Dict[str, Any]:
        """
        获取训练超参数预设

        Args:
            preset: 预设名称 (default, fast, accurate, augmented)

        Returns:
            超参数字典
        """
        presets = {
            "default": {
                "epochs": 100,
                "batch_size": 16,
                "imgsz": 640,
                "lr0": 0.01,
                "lrf": 0.01,
                "momentum": 0.937,
                "weight_decay": 0.0005,
                "warmup_epochs": 3.0,
                "patience": 100,
                "close_mosaic": 10,
            },
            "fast": {
                "epochs": 50,
                "batch_size": 32,
                "imgsz": 640,
                "lr0": 0.01,
                "lrf": 0.1,
                "momentum": 0.937,
                "weight_decay": 0.0005,
                "warmup_epochs": 1.0,
                "patience": 20,
                "close_mosaic": 5,
            },
            "accurate": {
                "epochs": 300,
                "batch_size": 8,
                "imgsz": 1024,
                "lr0": 0.005,
                "lrf": 0.001,
                "momentum": 0.937,
                "weight_decay": 0.0005,
                "warmup_epochs": 5.0,
                "patience": 100,
                "close_mosaic": 20,
            },
            "augmented": {
                "epochs": 150,
                "batch_size": 16,
                "imgsz": 640,
                "lr0": 0.01,
                "lrf": 0.01,
                "momentum": 0.937,
                "weight_decay": 0.0005,
                "warmup_epochs": 3.0,
                "patience": 100,
                "close_mosaic": 10,
                # 数据增强
                "hsv_h": 0.015,
                "hsv_s": 0.7,
                "hsv_v": 0.4,
                "degrees": 10.0,
                "translate": 0.1,
                "scale": 0.5,
                "shear": 0.0,
                "perspective": 0.0,
                "flipud": 0.0,
                "fliplr": 0.5,
                "mosaic": 1.0,
                "mixup": 0.1,
            },
        }

        if preset not in presets:
            logger.warning(f"Unknown preset: {preset}, using 'default'")
            preset = "default"

        return presets[preset]


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("YOLO Trainer Test")
    print("=" * 60)

    # 获取超参数预设
    for preset_name in ["default", "fast", "accurate", "augmented"]:
        params = YOLOTrainer.get_training_hyperparameters(preset_name)
        print(f"\n{preset_name.upper()} preset:")
        print(f"  epochs: {params['epochs']}")
        print(f"  batch_size: {params['batch_size']}")
        print(f"  lr0: {params['lr0']}")

    print("\n" + "=" * 60)
