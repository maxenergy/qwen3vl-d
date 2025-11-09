"""
Hunyuan Image 3.0 图片生成服务

支持本地部署和API调用两种模式
"""

import base64
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Literal, Tuple
from io import BytesIO

import httpx
from PIL import Image

from backend.core.config import settings
from backend.core.logging import logger


class HunyuanImageGenerator:
    """Hunyuan Image 3.0 图片生成器"""

    # 支持的分辨率
    SUPPORTED_RESOLUTIONS = {
        "640x640": (640, 640),
        "1024x1024": (1024, 1024),
        "1280x1280": (1280, 1280),
    }

    def __init__(
        self,
        api_url: Optional[str] = None,
        model_path: Optional[str] = None,
        use_local: bool = False,
        timeout: int = 300,
    ):
        """
        初始化Hunyuan图片生成器

        Args:
            api_url: API服务地址（API模式）
            model_path: 本地模型路径（本地模式）
            use_local: 是否使用本地部署模式
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url or settings.hunyuan_api_url
        self.model_path = model_path or settings.hunyuan_model_path
        self.use_local = use_local
        self.timeout = timeout

        # HTTP客户端（API模式）
        if not self.use_local and self.api_url:
            self.client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        else:
            self.client = None

        # 本地模型（本地模式）
        self.model = None
        if self.use_local:
            self._load_local_model()

    def _load_local_model(self):
        """加载本地Hunyuan模型"""
        try:
            logger.info(f"Loading Hunyuan model from {self.model_path}")
            # TODO: 实际加载模型的代码
            # 这里需要根据Hunyuan官方提供的Python SDK实现
            # from hunyuan_image import HunyuanImageModel
            # self.model = HunyuanImageModel.from_pretrained(self.model_path)
            logger.info("Hunyuan model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Hunyuan model: {e}")
            raise RuntimeError(f"Failed to load local Hunyuan model: {e}")

    async def generate_text_to_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "1024x1024",
        seed: Optional[int] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        **kwargs,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        文本生成图片

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            resolution: 图片分辨率，如 "1024x1024"
            seed: 随机种子
            num_inference_steps: 推理步数
            guidance_scale: 引导强度
            **kwargs: 其他参数

        Returns:
            (生成的图片, 生成参数字典)
        """
        if resolution not in self.SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"Unsupported resolution: {resolution}. "
                f"Supported: {list(self.SUPPORTED_RESOLUTIONS.keys())}"
            )

        width, height = self.SUPPORTED_RESOLUTIONS[resolution]

        # 生成参数
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed if seed is not None else int(time.time() * 1000) % 2**32,
            **kwargs,
        }

        logger.info(f"Generating image with params: {params}")

        if self.use_local:
            image = await self._generate_local(params)
        else:
            image = await self._generate_api(params)

        return image, params

    async def generate_image_to_image(
        self,
        prompt: str,
        input_image: Image.Image,
        negative_prompt: Optional[str] = None,
        resolution: str = "1024x1024",
        strength: float = 0.75,
        seed: Optional[int] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        **kwargs,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        图片+文本生成图片

        Args:
            prompt: 正向提示词
            input_image: 输入图片
            negative_prompt: 负向提示词
            resolution: 目标分辨率
            strength: 变换强度 (0-1)，越大变化越多
            seed: 随机种子
            num_inference_steps: 推理步数
            guidance_scale: 引导强度
            **kwargs: 其他参数

        Returns:
            (生成的图片, 生成参数字典)
        """
        if resolution not in self.SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"Unsupported resolution: {resolution}. "
                f"Supported: {list(self.SUPPORTED_RESOLUTIONS.keys())}"
            )

        width, height = self.SUPPORTED_RESOLUTIONS[resolution]

        # 调整输入图片尺寸
        input_image = input_image.resize((width, height), Image.Resampling.LANCZOS)

        # 生成参数
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "strength": strength,
            "seed": seed if seed is not None else int(time.time() * 1000) % 2**32,
            "mode": "image_to_image",
            **kwargs,
        }

        logger.info(f"Generating image-to-image with params: {params}")

        if self.use_local:
            image = await self._generate_local(params, input_image=input_image)
        else:
            image = await self._generate_api(params, input_image=input_image)

        return image, params

    async def _generate_local(
        self,
        params: Dict[str, Any],
        input_image: Optional[Image.Image] = None,
    ) -> Image.Image:
        """使用本地模型生成图片"""
        if self.model is None:
            raise RuntimeError("Local model not loaded")

        try:
            # TODO: 使用本地模型生成
            # 这里需要根据Hunyuan官方SDK实现
            # if input_image:
            #     result = self.model.img2img(**params, image=input_image)
            # else:
            #     result = self.model.text2img(**params)
            # return result.images[0]

            raise NotImplementedError(
                "Local model generation not implemented yet. "
                "Please use API mode or implement local model loading."
            )
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            raise RuntimeError(f"Failed to generate image locally: {e}")

    async def _generate_api(
        self,
        params: Dict[str, Any],
        input_image: Optional[Image.Image] = None,
        max_retries: int = 3,
    ) -> Image.Image:
        """使用API生成图片"""
        if self.client is None:
            raise RuntimeError("HTTP client not initialized")

        # 准备请求数据
        request_data = {
            "prompt": params["prompt"],
            "negative_prompt": params.get("negative_prompt", ""),
            "width": params["width"],
            "height": params["height"],
            "num_inference_steps": params.get("num_inference_steps", 50),
            "guidance_scale": params.get("guidance_scale", 7.5),
            "seed": params["seed"],
        }

        # 如果有输入图片，转换为base64
        if input_image:
            buffered = BytesIO()
            input_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            request_data["image"] = img_base64
            request_data["strength"] = params.get("strength", 0.75)

        # 重试逻辑
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"API generation attempt {attempt + 1}/{max_retries}")

                response = await self.client.post(
                    "/generate",
                    json=request_data,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # 解析响应
                result = response.json()

                if "image" in result:
                    # Base64编码的图片
                    image_data = base64.b64decode(result["image"])
                    image = Image.open(BytesIO(image_data))
                    logger.info("Image generated successfully via API")
                    return image
                elif "url" in result:
                    # 图片URL
                    img_response = await self.client.get(result["url"])
                    img_response.raise_for_status()
                    image = Image.open(BytesIO(img_response.content))
                    logger.info("Image downloaded successfully from URL")
                    return image
                else:
                    raise ValueError("Invalid API response: no image data found")

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"API timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"API HTTP error on attempt {attempt + 1}: {e}")
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    # 服务器错误，重试
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # 客户端错误或最后一次尝试，直接抛出
                    raise RuntimeError(f"API error: {e.response.text}")
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)

        # 所有重试都失败
        raise RuntimeError(f"Failed to generate image after {max_retries} attempts: {last_error}")

    async def save_image(
        self,
        image: Image.Image,
        output_dir: str,
        filename: Optional[str] = None,
        format: str = "PNG",
    ) -> str:
        """
        保存生成的图片

        Args:
            image: PIL图片对象
            output_dir: 输出目录
            filename: 文件名（不含后缀），如果为None则自动生成
            format: 图片格式（PNG, JPEG等）

        Returns:
            保存的文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = int(time.time() * 1000)
            filename = f"hunyuan_{timestamp}"

        file_path = output_path / f"{filename}.{format.lower()}"

        try:
            image.save(file_path, format=format)
            logger.info(f"Image saved to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise RuntimeError(f"Failed to save image: {e}")

    async def batch_generate(
        self,
        prompts: list[str],
        mode: Literal["text_to_image", "image_to_image"] = "text_to_image",
        input_images: Optional[list[Image.Image]] = None,
        **common_params,
    ) -> list[Tuple[Image.Image, Dict[str, Any]]]:
        """
        批量生成图片

        Args:
            prompts: 提示词列表
            mode: 生成模式
            input_images: 输入图片列表（image_to_image模式）
            **common_params: 公共参数

        Returns:
            [(图片, 参数字典), ...]
        """
        if mode == "image_to_image":
            if not input_images or len(input_images) != len(prompts):
                raise ValueError(
                    "image_to_image mode requires input_images with same length as prompts"
                )

        results = []
        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"Generating image {i + 1}/{len(prompts)}")

                if mode == "text_to_image":
                    image, params = await self.generate_text_to_image(
                        prompt=prompt,
                        **common_params,
                    )
                else:
                    image, params = await self.generate_image_to_image(
                        prompt=prompt,
                        input_image=input_images[i],
                        **common_params,
                    )

                results.append((image, params))

            except Exception as e:
                logger.error(f"Failed to generate image {i + 1}: {e}")
                results.append((None, {"error": str(e)}))

        return results

    async def close(self):
        """关闭资源"""
        if self.client:
            await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 导入asyncio用于重试逻辑
import asyncio
