#!/usr/bin/env python3
"""
Multi-category object detection using Qwen3-VL
Detects multiple object categories in a single image
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from utils import parse_json_response, plot_bounding_boxes

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"
MODEL_NAME = "qwen3-vl-30b"


def detect_objects(image_path, categories, api_base_url=API_BASE_URL, model_name=MODEL_NAME):
    """
    Detect multiple object categories in an image
    
    Args:
        image_path: Path to image file
        categories: List of categories to detect (e.g., ["car", "person", "bicycle"])
                   Can also be a comma-separated string
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
    
    # Parse categories
    if isinstance(categories, str):
        categories = [cat.strip() for cat in categories.split(",")]
    
    categories_str = ", ".join([f'"{cat}"' for cat in categories])
    
    # Prepare prompt
    prompt = f'''Locate every instance that belongs to the following categories: {categories_str}. Report bbox coordinates in JSON format like this:
{{"bbox_2d": [x1, y1, x2, y2], "label": "category_name"}}'''
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",
        base_url=api_base_url
    )
    
    # Call API
    print(f"\nDetecting objects in categories: {categories}")
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
    category_counts = {}
    for det in detections:
        label = det.get("label", "unknown")
        category_counts[label] = category_counts.get(label, 0) + 1
    
    print(f"\nFound {len(detections)} objects:")
    for category, count in sorted(category_counts.items()):
        print(f"  - {category}: {count}")
    
    return detections, image, width, height


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect multiple object categories in an image')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--categories', '-c', required=True, 
                       help='Comma-separated list of categories to detect (e.g., "car,person,bicycle")')
    parser.add_argument('--output', '-o', default='output_objects.jpg',
                       help='Output image path (default: output_objects.jpg)')
    parser.add_argument('--api-url', default=API_BASE_URL,
                       help=f'API base URL (default: {API_BASE_URL})')
    parser.add_argument('--model', default=MODEL_NAME,
                       help=f'Model name (default: {MODEL_NAME})')
    
    args = parser.parse_args()
    
    # Detect objects
    detections, image, width, height = detect_objects(
        args.image, 
        args.categories,
        args.api_url,
        args.model
    )
    
    # Draw and save
    plot_bounding_boxes(image, detections, args.output)
    
    print(f"\nDone! Open {args.output} to see the results.")


if __name__ == "__main__":
    main()
