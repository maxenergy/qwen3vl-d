#!/usr/bin/env python3
"""
Detailed people detection using Qwen3-VL
Detects people with body parts and attributes
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from utils import parse_json_response, plot_bounding_boxes

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"
MODEL_NAME = "qwen3-vl-30b"


def detect_people(image_path, include_parts=True, api_base_url=API_BASE_URL, model_name=MODEL_NAME):
    """
    Detect people with optional body parts detection
    
    Args:
        image_path: Path to image file
        include_parts: Whether to detect body parts (head, hand, etc.)
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
    
    # Prepare prompt based on options
    if include_parts:
        categories = '"head", "hand", "person", "man", "woman", "glasses"'
        prompt = f'''Locate every instance that belongs to the following categories: {categories}. Report bbox coordinates in JSON format like this:
{{"bbox_2d": [x1, y1, x2, y2], "label": "category_name"}}'''
    else:
        categories = '"person", "man", "woman"'
        prompt = f'''Locate every instance that belongs to the following categories: {categories}. Report bbox coordinates in JSON format like this:
{{"bbox_2d": [x1, y1, x2, y2], "label": "category_name"}}'''
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",
        base_url=api_base_url
    )
    
    # Call API
    print(f"\nDetecting people{'with body parts' if include_parts else ''}...")
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
    
    print(f"\nFound {len(detections)} detections:")
    for category, count in sorted(category_counts.items()):
        print(f"  - {category}: {count}")
    
    return detections, image, width, height


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect people with optional body parts')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--no-parts', action='store_true',
                       help='Disable body parts detection (only detect people)')
    parser.add_argument('--output', '-o', default='output_people.jpg',
                       help='Output image path (default: output_people.jpg)')
    parser.add_argument('--api-url', default=API_BASE_URL,
                       help=f'API base URL (default: {API_BASE_URL})')
    parser.add_argument('--model', default=MODEL_NAME,
                       help=f'Model name (default: {MODEL_NAME})')
    
    args = parser.parse_args()
    
    # Detect people
    detections, image, width, height = detect_people(
        args.image,
        include_parts=not args.no_parts,
        api_base_url=args.api_url,
        model_name=args.model
    )
    
    # Draw and save
    plot_bounding_boxes(image, detections, args.output)
    
    print(f"\nDone! Open {args.output} to see the results.")


if __name__ == "__main__":
    main()
