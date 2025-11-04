#!/usr/bin/env python3
"""
Shared utilities for Qwen3-VL object detection
"""

import json
import ast
from PIL import Image, ImageDraw, ImageFont

# Extended color palette
COLORS = [
    'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'brown', 
    'gray', 'beige', 'turquoise', 'cyan', 'magenta', 'lime', 'navy', 'maroon', 
    'teal', 'olive', 'coral', 'lavender', 'violet', 'gold', 'silver'
]


def parse_json_response(text):
    """Parse JSON from model response, removing markdown fencing if present"""
    # Remove markdown fencing
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "```json":
                text = "\n".join(lines[i+1:])
                text = text.split("```")[0]
                break
    
    text = text.strip()
    
    # Try to parse as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback to ast.literal_eval for malformed JSON
        try:
            return ast.literal_eval(text)
        except:
            # Last resort: try to find valid JSON array in text
            end_idx = text.rfind('"}') + len('"}')
            if end_idx > len('"}'):
                truncated_text = text[:end_idx] + "]"
                return ast.literal_eval(truncated_text)
            raise ValueError(f"Could not parse JSON from response: {text[:100]}...")


def get_font(size=14):
    """Get font for text rendering, with fallback options"""
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:\\Windows\\Fonts\\arial.ttf",  # Windows
    ]
    
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Fallback to default font
    return ImageFont.load_default()


def plot_bounding_boxes(image, detections, output_path=None):
    """
    Draw bounding boxes on image with labels
    
    Args:
        image: PIL Image object
        detections: List of detection dicts with bbox_2d and label
        output_path: Optional path to save output image
    
    Returns:
        PIL Image with bounding boxes drawn
    """
    if isinstance(image, str):
        image = Image.open(image)
    
    image = image.copy()  # Don't modify original
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = get_font(size=16)
    
    # Ensure detections is a list
    if not isinstance(detections, list):
        detections = [detections]
    
    print(f"\nDrawing {len(detections)} bounding boxes on {width}x{height} image")
    
    for i, detection in enumerate(detections):
        # Get color
        color = COLORS[i % len(COLORS)]
        
        # Convert normalized coordinates (0-1000) to absolute
        bbox = detection.get("bbox_2d", [])
        if len(bbox) != 4:
            print(f"Warning: Invalid bbox for detection {i}: {bbox}")
            continue
            
        x1 = int(bbox[0] / 1000 * width)
        y1 = int(bbox[1] / 1000 * height)
        x2 = int(bbox[2] / 1000 * width)
        y2 = int(bbox[3] / 1000 * height)
        
        # Ensure correct order
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Draw bounding box
        draw.rectangle(((x1, y1), (x2, y2)), outline=color, width=3)
        
        # Prepare label text
        label_parts = [detection.get("label", f"object_{i+1}")]
        
        # Add additional attributes if present
        if "type" in detection:
            label_parts.append(f"type:{detection['type']}")
        if "color" in detection and detection.get("label") != "color":
            label_parts.append(f"color:{detection['color']}")
        if "role" in detection:
            label_parts.append(f"role:{detection['role']}")
        if "shirt_color" in detection:
            label_parts.append(f"shirt:{detection['shirt_color']}")
        
        label_text = " ".join(label_parts)
        
        # Draw label background for better visibility
        bbox_text = draw.textbbox((x1 + 5, y1 + 5), label_text, font=font)
        draw.rectangle(bbox_text, fill=color)
        
        # Draw label text
        draw.text((x1 + 5, y1 + 5), label_text, fill='white', font=font)
        
        print(f"  {i+1}. {label_text} at [{x1}, {y1}, {x2}, {y2}]")
    
    # Save if output path provided
    if output_path:
        image.save(output_path)
        print(f"\nSaved result to: {output_path}")
    
    return image


def plot_points(image, detections, output_path=None):
    """
    Draw points on image with labels
    
    Args:
        image: PIL Image object or path
        detections: List of detection dicts with point_2d and label
        output_path: Optional path to save output image
    
    Returns:
        PIL Image with points drawn
    """
    if isinstance(image, str):
        image = Image.open(image)
    
    image = image.copy()  # Don't modify original
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = get_font(size=14)
    
    # Ensure detections is a list
    if not isinstance(detections, list):
        detections = [detections]
    
    print(f"\nDrawing {len(detections)} points on {width}x{height} image")
    
    for i, detection in enumerate(detections):
        # Get color
        color = COLORS[i % len(COLORS)]
        
        # Get point coordinates
        point = detection.get("point_2d", [])
        if len(point) != 2:
            print(f"Warning: Invalid point for detection {i}: {point}")
            continue
        
        # Convert normalized coordinates (0-1000) to absolute
        x = int(point[0] / 1000 * width)
        y = int(point[1] / 1000 * height)
        
        # Draw point as small circle
        radius = 4
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], 
                     fill=color, outline='white', width=2)
        
        # Prepare label text
        label_parts = [detection.get("label", f"point_{i+1}")]
        
        # Add additional attributes if present
        if "role" in detection:
            label_parts.append(f"({detection['role']})")
        if "shirt_color" in detection:
            label_parts.append(f"[{detection['shirt_color']}]")
        if "color" in detection and detection.get("label") != "color":
            label_parts.append(f"[{detection['color']}]")
        
        label_text = " ".join(label_parts)
        
        # Draw label with background
        text_pos = (x + 8, y + 8)
        bbox_text = draw.textbbox(text_pos, label_text, font=font)
        draw.rectangle(bbox_text, fill=color)
        draw.text(text_pos, label_text, fill='white', font=font)
        
        print(f"  {i+1}. {label_text} at ({x}, {y})")
    
    # Save if output path provided
    if output_path:
        image.save(output_path)
        print(f"\nSaved result to: {output_path}")
    
    return image


def create_thumbnail(image, max_size=640):
    """Create a thumbnail of the image for display"""
    if isinstance(image, str):
        image = Image.open(image)
    
    image = image.copy()
    image.thumbnail([max_size, max_size], Image.Resampling.LANCZOS)
    return image
