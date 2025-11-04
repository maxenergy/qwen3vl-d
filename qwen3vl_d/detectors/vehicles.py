"""Vehicle detector with attributes implementation."""

from typing import Dict, List, Union, Any
from PIL import Image
from .base import BaseDetector
from ..visualization import parse_json_response


class VehicleDetector(BaseDetector):
    """Detector for vehicles with type and color attributes."""
    
    def _build_prompt(self, **kwargs) -> str:
        """Build prompt for vehicle detection with attributes."""
        return '''Locate every instance that belongs to the following categories: "vehicle". For each vehicle, report bbox coordinates, vehicle type and vehicle color in JSON format like this:
{"bbox_2d": [x1, y1, x2, y2], "label": "vehicle", "type": "car/bus/truck/bicycle/motorcycle", "color": "vehicle_color"}'''
    
    def detect(
        self,
        image_input: Union[str, Image.Image],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Detect vehicles with type and color attributes.
        
        Args:
            image_input: Path to image or PIL Image object
            **kwargs: Additional parameters
            
        Returns:
            List of vehicle detections with bbox_2d, label, type, and color
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
