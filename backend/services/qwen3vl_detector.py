"""
Qwen3-VL目标检测客户端服务
Qwen3-VL Object Detection Client Service

与Qwen3-VL API交互，实现自动标注功能
"""

import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO

import httpx
from PIL import Image

from backend.core.config import settings
from backend.core.logging import logger


class BoundingBox:
    """边界框类"""

    def __init__(
        self,
        label: str,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        confidence: float = 1.0,
        coordinate_system: str = "qwen",  # qwen (0-1000) or normalized (0-1)
    ):
        """
        初始化边界框

        Args:
            label: 标签名称
            x_min, y_min, x_max, y_max: 坐标值
            confidence: 置信度
            coordinate_system: 坐标系统 (qwen: 0-1000, normalized: 0-1)
        """
        self.label = label
        self.confidence = confidence
        self.coordinate_system = coordinate_system

        # 存储原始坐标
        if coordinate_system == "qwen":
            # Qwen3-VL格式: 0-1000
            self.x_min_qwen = float(x_min)
            self.y_min_qwen = float(y_min)
            self.x_max_qwen = float(x_max)
            self.y_max_qwen = float(y_max)

            # 转换为归一化坐标 (0-1)
            self.x_min = x_min / 1000.0
            self.y_min = y_min / 1000.0
            self.x_max = x_max / 1000.0
            self.y_max = y_max / 1000.0
        else:
            # 已经是归一化坐标
            self.x_min = float(x_min)
            self.y_min = float(y_min)
            self.x_max = float(x_max)
            self.y_max = float(y_max)

            # 转换为Qwen格式
            self.x_min_qwen = x_min * 1000.0
            self.y_min_qwen = y_min * 1000.0
            self.x_max_qwen = x_max * 1000.0
            self.y_max_qwen = y_max * 1000.0

    @property
    def center_x(self) -> float:
        """中心点X坐标（归一化）"""
        return (self.x_min + self.x_max) / 2.0

    @property
    def center_y(self) -> float:
        """中心点Y坐标（归一化）"""
        return (self.y_min + self.y_max) / 2.0

    @property
    def width(self) -> float:
        """宽度（归一化）"""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """高度（归一化）"""
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        """面积（归一化）"""
        return self.width * self.height

    def to_yolo_format(self) -> Tuple[float, float, float, float]:
        """
        转换为YOLO格式 (center_x, center_y, width, height)
        所有值都是归一化的 (0-1)

        Returns:
            (center_x, center_y, width, height)
        """
        return (self.center_x, self.center_y, self.width, self.height)

    def to_coco_format(self, image_width: int, image_height: int) -> Tuple[int, int, int, int]:
        """
        转换为COCO格式 (x, y, width, height)
        使用绝对像素坐标

        Args:
            image_width: 图片宽度
            image_height: 图片高度

        Returns:
            (x, y, width, height) in pixels
        """
        x = int(self.x_min * image_width)
        y = int(self.y_min * image_height)
        w = int(self.width * image_width)
        h = int(self.height * image_height)
        return (x, y, w, h)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "label": self.label,
            "confidence": self.confidence,
            "bbox": {
                "x_min": self.x_min,
                "y_min": self.y_min,
                "x_max": self.x_max,
                "y_max": self.y_max,
            },
            "bbox_qwen": {
                "x_min": self.x_min_qwen,
                "y_min": self.y_min_qwen,
                "x_max": self.x_max_qwen,
                "y_max": self.y_max_qwen,
            },
            "center": {"x": self.center_x, "y": self.center_y},
            "size": {"width": self.width, "height": self.height},
            "area": self.area,
        }

    def __repr__(self) -> str:
        return (
            f"BoundingBox(label='{self.label}', "
            f"bbox=({self.x_min:.3f}, {self.y_min:.3f}, {self.x_max:.3f}, {self.y_max:.3f}), "
            f"confidence={self.confidence:.3f})"
        )


class DetectionResult:
    """检测结果类"""

    def __init__(self, image_id: Optional[int] = None):
        self.image_id = image_id
        self.bboxes: List[BoundingBox] = []
        self.raw_response: Optional[Dict[str, Any]] = None

    def add_bbox(self, bbox: BoundingBox):
        """添加边界框"""
        self.bboxes.append(bbox)

    def filter_by_label(self, labels: List[str]) -> "DetectionResult":
        """根据标签筛选"""
        result = DetectionResult(self.image_id)
        result.bboxes = [bbox for bbox in self.bboxes if bbox.label in labels]
        result.raw_response = self.raw_response
        return result

    def filter_by_confidence(self, min_confidence: float) -> "DetectionResult":
        """根据置信度筛选"""
        result = DetectionResult(self.image_id)
        result.bboxes = [bbox for bbox in self.bboxes if bbox.confidence >= min_confidence]
        result.raw_response = self.raw_response
        return result

    def get_labels_count(self) -> Dict[str, int]:
        """统计各标签数量"""
        counts = {}
        for bbox in self.bboxes:
            counts[bbox.label] = counts.get(bbox.label, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "image_id": self.image_id,
            "total_objects": len(self.bboxes),
            "labels_count": self.get_labels_count(),
            "bboxes": [bbox.to_dict() for bbox in self.bboxes],
        }

    def __len__(self) -> int:
        return len(self.bboxes)

    def __repr__(self) -> str:
        return f"DetectionResult(objects={len(self.bboxes)}, labels={list(self.get_labels_count().keys())})"


class Qwen3VLClient:
    """Qwen3-VL客户端"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        初始化Qwen3-VL客户端

        Args:
            api_url: API地址
            api_key: API密钥
            model: 模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url or settings.qwen3vl_api_url
        self.api_key = api_key or settings.qwen3vl_api_key
        self.model = model or settings.qwen3vl_model
        self.timeout = timeout

        # HTTP客户端
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )

    async def detect_objects(
        self,
        image: Image.Image,
        labels: List[str],
        prompt_template: Optional[str] = None,
        confidence_threshold: float = 0.5,
        max_retries: int = 3,
    ) -> DetectionResult:
        """
        检测图片中的目标

        Args:
            image: PIL图片对象
            labels: 要检测的标签列表
            prompt_template: 提示词模板（可选）
            confidence_threshold: 置信度阈值
            max_retries: 最大重试次数

        Returns:
            DetectionResult对象
        """
        # 构建检测提示词
        if prompt_template:
            prompt = prompt_template.format(labels=", ".join(labels))
        else:
            prompt = self._build_detection_prompt(labels)

        # 图片转base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # 准备请求
        request_data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img_base64},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "temperature": 0.1,  # 低温度获得更确定的结果
            "max_tokens": 4096,
        }

        # 重试逻辑
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Qwen3-VL detection attempt {attempt + 1}/{max_retries}")

                response = await self.client.post(
                    "/chat/completions",
                    json=request_data,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # 解析响应
                result_data = response.json()
                detection_result = self._parse_detection_response(
                    result_data,
                    labels,
                    confidence_threshold,
                )

                logger.info(f"Detected {len(detection_result)} objects: {detection_result}")
                return detection_result

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Qwen3-VL timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"Qwen3-VL HTTP error on attempt {attempt + 1}: {e}")
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    import asyncio
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError(f"Qwen3-VL API error: {e.response.text}")
            except Exception as e:
                last_error = e
                logger.error(f"Qwen3-VL unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)

        raise RuntimeError(f"Failed to detect objects after {max_retries} attempts: {last_error}")

    async def batch_detect(
        self,
        images: List[Image.Image],
        labels: List[str],
        **kwargs,
    ) -> List[DetectionResult]:
        """
        批量检测

        Args:
            images: 图片列表
            labels: 标签列表
            **kwargs: 传递给detect_objects的其他参数

        Returns:
            DetectionResult列表
        """
        results = []
        for i, image in enumerate(images):
            try:
                logger.info(f"Batch detection {i+1}/{len(images)}")
                result = await self.detect_objects(image, labels, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to detect image {i+1}: {e}")
                # 添加空结果
                empty_result = DetectionResult()
                results.append(empty_result)

        return results

    def _build_detection_prompt(self, labels: List[str]) -> str:
        """
        构建检测提示词

        Args:
            labels: 标签列表

        Returns:
            提示词字符串
        """
        labels_str = ", ".join(labels)
        prompt = (
            f"Please detect all objects in the image that belong to the following categories: {labels_str}. "
            f"For each detected object, provide the bounding box coordinates in the format: "
            f"<ref>label</ref><box>(x1,y1),(x2,y2)</box>, where coordinates are in the range [0, 1000]. "
            f"List all detected objects."
        )
        return prompt

    def _parse_detection_response(
        self,
        response: Dict[str, Any],
        target_labels: List[str],
        confidence_threshold: float,
    ) -> DetectionResult:
        """
        解析检测响应

        Args:
            response: API响应
            target_labels: 目标标签列表
            confidence_threshold: 置信度阈值

        Returns:
            DetectionResult对象
        """
        result = DetectionResult()
        result.raw_response = response

        try:
            # 获取模型输出文本
            choices = response.get("choices", [])
            if not choices:
                logger.warning("No choices in response")
                return result

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                logger.warning("Empty content in response")
                return result

            # 解析边界框
            # 格式: <ref>label</ref><box>(x1,y1),(x2,y2)</box>
            import re

            pattern = r'<ref>([^<]+)</ref><box>\((\d+),(\d+)\),\((\d+),(\d+)\)</box>'
            matches = re.findall(pattern, content)

            for match in matches:
                label, x1, y1, x2, y2 = match

                # 验证标签
                if label not in target_labels:
                    logger.debug(f"Skipping non-target label: {label}")
                    continue

                # 创建边界框
                try:
                    bbox = BoundingBox(
                        label=label,
                        x_min=float(x1),
                        y_min=float(y1),
                        x_max=float(x2),
                        y_max=float(y2),
                        confidence=1.0,  # Qwen3-VL默认没有置信度，设为1.0
                        coordinate_system="qwen",
                    )

                    # 验证坐标有效性
                    if self._validate_bbox(bbox):
                        result.add_bbox(bbox)
                    else:
                        logger.warning(f"Invalid bbox: {bbox}")

                except Exception as e:
                    logger.error(f"Failed to parse bbox: {e}")
                    continue

            logger.info(f"Parsed {len(result)} bounding boxes from response")

        except Exception as e:
            logger.error(f"Failed to parse detection response: {e}")

        return result

    def _validate_bbox(self, bbox: BoundingBox) -> bool:
        """
        验证边界框有效性

        Args:
            bbox: 边界框对象

        Returns:
            是否有效
        """
        # 检查坐标范围
        if not (0 <= bbox.x_min <= 1 and 0 <= bbox.y_min <= 1):
            return False
        if not (0 <= bbox.x_max <= 1 and 0 <= bbox.y_max <= 1):
            return False

        # 检查最小值小于最大值
        if bbox.x_min >= bbox.x_max or bbox.y_min >= bbox.y_max:
            return False

        # 检查面积不为0
        if bbox.area <= 0:
            return False

        return True

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 创建全局客户端实例（可选）
_global_client: Optional[Qwen3VLClient] = None


def get_qwen3vl_client() -> Qwen3VLClient:
    """获取全局Qwen3-VL客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = Qwen3VLClient()
    return _global_client


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        client = Qwen3VLClient()

        # 创建测试图片
        test_image = Image.new("RGB", (640, 480), color="white")

        # 检测
        result = await client.detect_objects(
            test_image,
            labels=["person", "car", "dog"],
        )

        print(f"Detection result: {result}")
        print(f"Details: {result.to_dict()}")

        await client.close()

    asyncio.run(test())
