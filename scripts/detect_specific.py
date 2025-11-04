#!/usr/bin/env python3
"""
Description-based object detection using Qwen3-VL
Find specific objects using natural language descriptions
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from utils import parse_json_response, plot_bounding_boxes, plot_points

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"
MODEL_NAME = "qwen3-vl-30b"


def detect_specific(image_path, description, use_points=False, api_base_url=API_BASE_URL, model_name=MODEL_NAME):
    """
    Find a specific object using natural language description
    
    Args:
        image_path: Path to image file
        description: Natural language description of the object (e.g., "the brown cake in the top right corner")
        use_points: Whether to use point-based grounding instead of bounding boxes
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
    
    # Prepare prompt based on detection type
    if use_points:
        prompt = f'''Locate "{description}" with a point, output its point coordinates in JSON format like this:
{{"point_2d": [x, y], "label": "{description}"}}'''
    else:
        prompt = f'''Locate "{description}", output its bbox coordinates in JSON format like this:
{{"bbox_2d": [x1, y1, x2, y2], "label": "{description}"}}'''
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",
        base_url=api_base_url
    )
    
    # Call API
    print(f"\nSearching for: {description}")
    print(f"Using {'point' if use_points else 'bbox'} detection...")
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
    
    # Ensure it's a list
    if not isinstance(detections, list):
        detections = [detections]
    
    print(f"\nFound {len(detections)} match(es) for: {description}")
    
    return detections, image, width, height


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Find specific objects using natural language descriptions')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--description', '-d', required=True,
                       help='Natural language description of the object to find')
    parser.add_argument('--points', '-p', action='store_true',
                       help='Use point-based grounding instead of bounding boxes')
    parser.add_argument('--output', '-o', default='output_specific.jpg',
                       help='Output image path (default: output_specific.jpg)')
    parser.add_argument('--api-url', default=API_BASE_URL,
                       help=f'API base URL (default: {API_BASE_URL})')
    parser.add_argument('--model', default=MODEL_NAME,
                       help=f'Model name (default: {MODEL_NAME})')
    
    args = parser.parse_args()
    
    # Detect specific object
    detections, image, width, height = detect_specific(
        args.image,
        args.description,
        use_points=args.points,
        api_base_url=args.api_url,
        model_name=args.model
    )
    
    # Draw and save
    if args.points:
        plot_points(image, detections, args.output)
    else:
        plot_bounding_boxes(image, detections, args.output)
    
    print(f"\nDone! Open {args.output} to see the results.")


if __name__ == "__main__":
    main()
