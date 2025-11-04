#!/usr/bin/env python3
"""
Point-based object detection using Qwen3-VL
Detects objects and marks them with point coordinates instead of bounding boxes
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from utils import parse_json_response, plot_points

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"
MODEL_NAME = "qwen3-vl-30b"


def detect_with_points(image_path, category, attributes=None, api_base_url=API_BASE_URL, model_name=MODEL_NAME):
    """
    Detect objects using point-based grounding with optional attributes
    
    Args:
        image_path: Path to image file
        category: Category to detect (e.g., "person", "player")
        attributes: Dict of attributes to detect (e.g., {"role": "player/referee", "shirt_color": "color"})
        api_base_url: API endpoint URL
        model_name: Model name to use
    
    Returns:
        tuple: (detections list, PIL Image, width, height)
    """
    # Load and encode image
    image = Image.open(image_path)
    width, height = image.size
    print(f"Image size: {width}x{height}")
    
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Prepare prompt based on attributes
    if attributes:
        attr_desc = ", ".join([f'"{k}": "{v}"' for k, v in attributes.items()])
        prompt = f'''Locate every {category} with points, report their point coordinates and attributes in JSON format like this:
{{"point_2d": [x, y], "label": "{category}", {attr_desc}}}'''
    else:
        prompt = f'''Locate every {category} with points, report their point coordinates in JSON format like this:
{{"point_2d": [x, y], "label": "{category}"}}'''
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",
        base_url=api_base_url
    )
    
    # Call API
    print(f"\nDetecting {category} with point-based grounding...")
    print("Calling API...")
    
    completion = client.chat.completions.create(
        model=model_name,
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
    
    response_text = completion.choices[0].message.content
    print(f"\nRaw response:\n{response_text}\n")
    
    # Parse JSON response
    detections = parse_json_response(response_text)
    
    # Print summary
    print(f"\nFound {len(detections)} {category}(s)")
    
    if attributes:
        # Count by attributes
        for attr_name in attributes.keys():
            attr_counts = {}
            for det in detections:
                attr_value = det.get(attr_name, "unknown")
                attr_counts[attr_value] = attr_counts.get(attr_value, 0) + 1
            
            print(f"\nBy {attr_name}:")
            for value, count in sorted(attr_counts.items()):
                print(f"  - {value}: {count}")
    
    return detections, image, width, height


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Point-based object detection with optional attributes')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--category', '-c', required=True,
                       help='Category to detect (e.g., "person", "player")')
    parser.add_argument('--attributes', '-a', nargs='*',
                       help='Attributes to detect, format: key=value (e.g., role="player/referee" shirt_color=color)')
    parser.add_argument('--output', '-o', default='output_points.jpg',
                       help='Output image path (default: output_points.jpg)')
    parser.add_argument('--api-url', default=API_BASE_URL,
                       help=f'API base URL (default: {API_BASE_URL})')
    parser.add_argument('--model', default=MODEL_NAME,
                       help=f'Model name (default: {MODEL_NAME})')
    
    args = parser.parse_args()
    
    # Parse attributes
    attributes = {}
    if args.attributes:
        for attr in args.attributes:
            if '=' in attr:
                key, value = attr.split('=', 1)
                attributes[key.strip()] = value.strip()
    
    # Detect with points
    detections, image, width, height = detect_with_points(
        args.image,
        args.category,
        attributes if attributes else None,
        args.api_url,
        args.model
    )
    
    # Draw and save
    plot_points(image, detections, args.output)
    
    print(f"\nDone! Open {args.output} to see the results.")


if __name__ == "__main__":
    main()
