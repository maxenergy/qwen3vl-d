"""Detector classes for different detection types."""

from .base import BaseDetector
from .faces import FaceDetector
from .objects import ObjectDetector
from .vehicles import VehicleDetector
from .points import PointDetector

__all__ = [
    'BaseDetector',
    'FaceDetector',
    'ObjectDetector',
    'VehicleDetector',
    'PointDetector',
]
