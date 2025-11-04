"""qwen3vl-d - Qwen3-VL Object Detection Package.

A Python package for object detection using Qwen3-VL vision-language model
via local OpenAI-compatible API.
"""

from .client import Qwen3VLClient
from .visualization import plot_bounding_boxes, plot_points, parse_json_response
from .detectors import (
    BaseDetector,
    FaceDetector,
    ObjectDetector,
    VehicleDetector,
    PointDetector,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    'Qwen3VLClient',
    
    # Visualization functions
    'plot_bounding_boxes',
    'plot_points',
    'parse_json_response',
    
    # Detector classes
    'BaseDetector',
    'FaceDetector',
    'ObjectDetector',
    'VehicleDetector',
    'PointDetector',
]
