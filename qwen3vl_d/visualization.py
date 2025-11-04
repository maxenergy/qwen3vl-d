"""Visualization utilities for detection results."""

import json
from typing import Dict, List, Union, Optional, Any
from PIL import Image, ImageDraw, ImageFont


def parse_json_response(response_text: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse JSON response from API, handling markdown fences.
    
    Args:
        response_text: Raw API response text
        
    Returns:
        Parsed JSON (list or dict)
    """
    # Remove markdown fencing if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        # Handle plain ``` fences
        parts = response_text.split("```")
        if len(parts) >= 2:
            response_text = parts[1]
    
    # Parse JSON
    return json.loads(response_text.strip())


def plot_bounding_boxes(
    image_input: Union[str, Image.Image],
    detections: List[Dict[str, Any]],
    save_path: Optional[str] = None
) -> Image.Image:
    """
    Plot bounding boxes on image.
    
    Args:
        image_input: Path to image or PIL Image object
        detections: List of detection dictionaries with bbox_2d
        save_path: Optional path to save the result
        
    Returns:
        PIL Image with bounding boxes drawn
    """
    # Load image if path provided
    if isinstance(image_input, str):
        image = Image.open(image_input)
    else:
        image = image_input.copy()
    
    width, height = image.size
    draw = ImageDraw.Draw(image)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
    
    # Color palette
    colors = [
        'red', 'green', 'blue', 'yellow', 'orange', 'pink', 
        'purple', 'cyan', 'magenta', 'lime', 'coral', 'turquoise'
    ]
    
    # Draw each detection
    for i, detection in enumerate(detections):
        bbox = detection.get("bbox_2d", [])
        if len(bbox) != 4:
            continue
        
        # Convert normalized coords (0-1000) to absolute pixels
        x1 = int(bbox[0] / 1000 * width)
        y1 = int(bbox[1] / 1000 * height)
        x2 = int(bbox[2] / 1000 * width)
        y2 = int(bbox[3] / 1000 * height)
        
        # Ensure correct order
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Select color
        color = colors[i % len(colors)]
        
        # Draw bounding box
        draw.rectangle(((x1, y1), (x2, y2)), outline=color, width=3)
        
        # Draw label
        label = detection.get("label", "object")
        # Add type and color for vehicles if present
        if "type" in detection:
            label += f" ({detection['type']}"
            if "color" in detection:
                label += f", {detection['color']}"
            label += ")"
        
        draw.text((x1 + 5, y1 + 5), label, fill=color, font=font)
    
    # Save if path provided
    if save_path:
        image.save(save_path)
    
    return image


def plot_points(
    image_input: Union[str, Image.Image],
    points: List[Dict[str, Any]],
    save_path: Optional[str] = None
) -> Image.Image:
    """
    Plot points on image.
    
    Args:
        image_input: Path to image or PIL Image object
        points: List of point dictionaries with point_2d
        save_path: Optional path to save the result
        
    Returns:
        PIL Image with points drawn
    """
    # Load image if path provided
    if isinstance(image_input, str):
        image = Image.open(image_input)
    else:
        image = image_input.copy()
    
    width, height = image.size
    draw = ImageDraw.Draw(image)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()
    
    # Color palette
    colors = [
        'red', 'green', 'blue', 'yellow', 'orange', 'pink',
        'purple', 'cyan', 'magenta', 'lime', 'coral', 'turquoise'
    ]
    
    # Draw each point
    for i, point_data in enumerate(points):
        point = point_data.get("point_2d", [])
        if len(point) != 2:
            continue
        
        # Convert normalized coords (0-1000) to absolute pixels
        x = int(point[0] / 1000 * width)
        y = int(point[1] / 1000 * height)
        
        # Select color
        color = colors[i % len(colors)]
        
        # Draw point (small circle)
        radius = 4
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=color)
        
        # Draw label
        label = point_data.get("label", f"point_{i+1}")
        draw.text((x + 8, y + 8), label, fill=color, font=font)
    
    # Save if path provided
    if save_path:
        image.save(save_path)
    
    return image
