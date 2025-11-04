"""Face detector implementation."""

from typing import Dict, List, Union, Any
from PIL import Image
from .base import BaseDetector
from ..visualization import parse_json_response


class FaceDetector(BaseDetector):
    """Detector for faces in images."""
    
    def _build_prompt(self, **kwargs) -> str:
        """Build prompt for face detection."""
        return '''Locate every face in this image. For each face, report bbox coordinates in JSON format like this:
{"bbox_2d": [x1, y1, x2, y2], "label": "face"}'''
    
    def detect(
        self,
        image_input: Union[str, Image.Image],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Detect faces in image.
        
        Args:
            image_input: Path to image or PIL Image object
            **kwargs: Additional parameters (unused for face detection)
            
        Returns:
            List of face detections with bbox_2d and label
        """
        # Encode image
        image, base64_image = self._encode_image(image_input)
        
        # Build prompt
        prompt = self._build_prompt()
        
        # Call API
        response_text = self._call_api(base64_image, prompt)
        
        # Parse response
        detections = parse_json_response(response_text)
        
        # Ensure it's a list
        if not isinstance(detections, list):
            detections = [detections]
        
        return detections
