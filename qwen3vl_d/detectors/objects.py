"""Multi-category object detector implementation."""

from typing import Dict, List, Union, Any
from PIL import Image
from .base import BaseDetector
from ..visualization import parse_json_response


class ObjectDetector(BaseDetector):
    """Detector for multiple object categories."""
    
    def _build_prompt(self, categories: List[str], **kwargs) -> str:
        """
        Build prompt for multi-category object detection.
        
        Args:
            categories: List of categories to detect
        """
        categories_str = ", ".join([f'"{cat}"' for cat in categories])
        return f'''Locate every instance that belongs to the following categories: {categories_str}. Report bbox coordinates in JSON format like this:
{{"bbox_2d": [x1, y1, x2, y2], "label": "category_name"}}'''
    
    def detect(
        self,
        image_input: Union[str, Image.Image],
        categories: Union[List[str], str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Detect multiple object categories in image.
        
        Args:
            image_input: Path to image or PIL Image object
            categories: List of categories or comma-separated string
            **kwargs: Additional parameters
            
        Returns:
            List of object detections with bbox_2d and label
        """
        # Parse categories
        if isinstance(categories, str):
            categories = [cat.strip() for cat in categories.split(",")]
        
        # Encode image
        image, base64_image = self._encode_image(image_input)
        
        # Build prompt
        prompt = self._build_prompt(categories)
        
        # Call API
        response_text = self._call_api(base64_image, prompt)
        
        # Parse response
        detections = parse_json_response(response_text)
        
        # Ensure it's a list
        if not isinstance(detections, list):
            detections = [detections]
        
        return detections
