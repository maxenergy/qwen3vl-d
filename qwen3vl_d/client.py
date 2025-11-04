"""Main client for Qwen3-VL detection."""

from typing import Union, List, Optional, Tuple, Any, Dict
from PIL import Image
from openai import OpenAI

from .detectors import FaceDetector, ObjectDetector, VehicleDetector, PointDetector
from .visualization import plot_bounding_boxes, plot_points


class Qwen3VLClient:
    """Client for Qwen3-VL object detection via OpenAI-compatible API."""
    
    def __init__(
        self,
        api_url: str = "http://192.168.8.147:9292/v1",
        model_name: str = "qwen3-vl-30b",
        api_key: str = "not-needed"
    ):
        """
        Initialize Qwen3VL client.
        
        Args:
            api_url: Base URL for the API endpoint
            model_name: Model name to use for detection
            api_key: API key (optional for local servers)
        """
        self.api_url = api_url
        self.model_name = model_name
        
        # Initialize OpenAI client
        self._openai_client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        
        # Initialize detectors
        self._face_detector = FaceDetector(self._openai_client, model_name)
        self._object_detector = ObjectDetector(self._openai_client, model_name)
        self._vehicle_detector = VehicleDetector(self._openai_client, model_name)
        self._point_detector = PointDetector(self._openai_client, model_name)
    
    def detect_faces(
        self,
        image: Union[str, Image.Image],
        save_output: Optional[str] = None,
        visualize: bool = True
    ) -> Union[Tuple[List[Dict[str, Any]], Image.Image], List[Dict[str, Any]]]:
        """
        Detect faces in an image.
        
        Args:
            image: Path to image file or PIL Image object
            save_output: Optional path to save visualization
            visualize: Whether to create visualization (default: True)
            
        Returns:
            If visualize=True: Tuple of (detections list, visualized PIL Image)
            If visualize=False: List of detection dictionaries
            
        Example:
            >>> client = Qwen3VLClient()
            >>> detections, viz = client.detect_faces("photo.jpg")
            >>> print(f"Found {len(detections)} faces")
        """
        # Get detections
        detections = self._face_detector.detect(image)
        
        if not visualize:
            return detections
        
        # Create visualization
        viz_image = plot_bounding_boxes(image, detections, save_output)
        
        return detections, viz_image
    
    def detect_objects(
        self,
        image: Union[str, Image.Image],
        categories: Union[List[str], str],
        save_output: Optional[str] = None,
        visualize: bool = True
    ) -> Union[Tuple[List[Dict[str, Any]], Image.Image], List[Dict[str, Any]]]:
        """
        Detect multiple object categories in an image.
        
        Args:
            image: Path to image file or PIL Image object
            categories: List of categories or comma-separated string
            save_output: Optional path to save visualization
            visualize: Whether to create visualization (default: True)
            
        Returns:
            If visualize=True: Tuple of (detections list, visualized PIL Image)
            If visualize=False: List of detection dictionaries
            
        Example:
            >>> client = Qwen3VLClient()
            >>> detections, viz = client.detect_objects(
            ...     "image.jpg",
            ...     categories=["car", "person", "bicycle"]
            ... )
        """
        # Get detections
        detections = self._object_detector.detect(image, categories=categories)
        
        if not visualize:
            return detections
        
        # Create visualization
        viz_image = plot_bounding_boxes(image, detections, save_output)
        
        return detections, viz_image
    
    def detect_vehicles(
        self,
        image: Union[str, Image.Image],
        save_output: Optional[str] = None,
        visualize: bool = True
    ) -> Union[Tuple[List[Dict[str, Any]], Image.Image], List[Dict[str, Any]]]:
        """
        Detect vehicles with type and color attributes.
        
        Args:
            image: Path to image file or PIL Image object
            save_output: Optional path to save visualization
            visualize: Whether to create visualization (default: True)
            
        Returns:
            If visualize=True: Tuple of (detections list, visualized PIL Image)
            If visualize=False: List of detection dictionaries
            
        Each detection includes:
            - bbox_2d: Bounding box coordinates
            - label: "vehicle"
            - type: Vehicle type (car, bus, truck, bicycle, motorcycle)
            - color: Vehicle color
            
        Example:
            >>> client = Qwen3VLClient()
            >>> detections, viz = client.detect_vehicles("street.jpg")
            >>> for det in detections:
            ...     print(f"{det['color']} {det['type']}")
        """
        # Get detections
        detections = self._vehicle_detector.detect(image)
        
        if not visualize:
            return detections
        
        # Create visualization
        viz_image = plot_bounding_boxes(image, detections, save_output)
        
        return detections, viz_image
    
    def detect_points(
        self,
        image: Union[str, Image.Image],
        category: str,
        attributes: Optional[Dict[str, str]] = None,
        save_output: Optional[str] = None,
        visualize: bool = True
    ) -> Union[Tuple[List[Dict[str, Any]], Image.Image], List[Dict[str, Any]]]:
        """
        Detect objects using point-based grounding (center points instead of bounding boxes).
        
        Args:
            image: Path to image file or PIL Image object
            category: Category to detect (e.g., "person", "car", "ball")
            attributes: Optional dict of attributes to include in detection
                       e.g., {"role": "player/referee", "shirt_color": "color"}
            save_output: Optional path to save visualization
            visualize: Whether to create visualization (default: True)
            
        Returns:
            If visualize=True: Tuple of (detections list, visualized PIL Image)
            If visualize=False: List of detection dictionaries
            
        Each detection includes:
            - point_2d: Point coordinates [x, y]
            - label: Object category
            - Additional attributes if specified
            
        Example:
            >>> client = Qwen3VLClient()
            >>> # Simple point detection
            >>> detections, viz = client.detect_points("image.jpg", category="person")
            >>> 
            >>> # With attributes (like football players)
            >>> detections, viz = client.detect_points(
            ...     "football.jpg",
            ...     category="person",
            ...     attributes={"role": "player/referee", "shirt_color": "color"}
            ... )
            >>> for det in detections:
            ...     print(f"{det['role']} in {det['shirt_color']} shirt")
        """
        # Get detections
        detections = self._point_detector.detect(image, category=category, attributes=attributes)
        
        if not visualize:
            return detections
        
        # Create visualization with points
        viz_image = plot_points(image, detections, save_output)
        
        return detections, viz_image
