"""Base detector class for all detection types."""

import base64
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Any
from PIL import Image
from openai import OpenAI


class BaseDetector(ABC):
    """Abstract base class for all detectors."""
    
    def __init__(self, client: OpenAI, model_name: str):
        """
        Initialize detector.
        
        Args:
            client: OpenAI client instance
            model_name: Model name to use
        """
        self.client = client
        self.model_name = model_name
    
    def _encode_image(self, image_input: Union[str, Image.Image]) -> tuple[Image.Image, str]:
        """
        Encode image to base64.
        
        Args:
            image_input: Path to image or PIL Image object
            
        Returns:
            Tuple of (PIL Image, base64 string)
        """
        if isinstance(image_input, str):
            # Load from file path
            with open(image_input, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            # Convert PIL Image to base64
            from io import BytesIO
            buffer = BytesIO()
            image_input.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            image = image_input
        else:
            raise ValueError("image_input must be a file path or PIL Image")
        
        return image, base64_image
    
    def _call_api(self, base64_image: str, prompt: str) -> str:
        """
        Call OpenAI API.
        
        Args:
            base64_image: Base64 encoded image
            prompt: Text prompt
            
        Returns:
            API response text
        """
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        
        return completion.choices[0].message.content
    
    @abstractmethod
    def _build_prompt(self, **kwargs) -> str:
        """Build detection prompt. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def detect(self, image_input: Union[str, Image.Image], **kwargs) -> List[Dict[str, Any]]:
        """Perform detection. Must be implemented by subclasses."""
        pass
