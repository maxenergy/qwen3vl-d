"""Point-based detector implementation."""

from typing import Dict, List, Union, Any, Optional
from PIL import Image
from .base import BaseDetector
from ..visualization import parse_json_response


class PointDetector(BaseDetector):
    """Detector for point-based object grounding."""
    
    def _build_prompt(self, category: str, attributes: Optional[Dict[str, str]] = None, **kwargs) -> str:
        """
        Build prompt for point-based detection.
        
        Args:
            category: Category to detect (e.g., "person", "player")
            attributes: Optional dict of attributes to detect
        """
        if attributes:
            attr_desc = ", ".join([f'"{k}": "{v}"' for k, v in attributes.items()])
            return f'''Locate every {category} with points, report their point coordinates and attributes in JSON format like this:
{{"point_2d": [x, y], "label": "{category}", {attr_desc}}}'''
        else:
            return f'''Locate every {category} with points, report their point coordinates in JSON format like this:
{{"point_2d": [x, y], "label": "{category}"}}'''
    
    def detect(
        self,
        image_input: Union[str, Image.Image],
        category: str,
        attributes: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Detect objects using point-based grounding.
        
        Args:
            image_input: Path to image or PIL Image object
            category: Category to detect (e.g., "person", "car", "ball")
            attributes: Optional dict of attributes to include in detection
                       e.g., {"role": "player/referee", "shirt_color": "color"}
            **kwargs: Additional parameters
            
        Returns:
            List of point detections with point_2d, label, and optional attributes
            
        Example:
            >>> detector.detect("image.jpg", category="person")
            [{"point_2d": [500, 300], "label": "person"}, ...]
            
            >>> detector.detect("image.jpg", category="person", 
            ...                attributes={"role": "player/referee", "shirt_color": "color"})
            [{"point_2d": [500, 300], "label": "person", "role": "player", "shirt_color": "red"}, ...]
        """
        # Encode image
        image, base64_image = self._encode_image(image_input)
        
        # Build prompt
        prompt = self._build_prompt(category, attributes)
        
        # Call API
        response_text = self._call_api(base64_image, prompt)
        
        # Parse response
        detections = parse_json_response(response_text)
        
        # Ensure it's a list
        if not isinstance(detections, list):
            detections = [detections]
        
        return detections
