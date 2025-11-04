#!/usr/bin/env python3
"""
Vehicle detection with attributes using Qwen3-VL
Detects vehicles and reports their type and color
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from utils import parse_json_response, plot_bounding_boxes

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"
MODEL_NAME = "qwen3-vl-30b"


def detect_vehicles(image_path, api_base_url=API_BASE_URL, model_name=MODEL_NAME):
    """
    Detect vehicles with type and color attributes
    
    Args:
        image_path: Path to image file
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
    
    # Prepare prompt
    prompt = '''Locate every instance that belongs to the following categories: "vehicle". For each vehicle, report bbox coordinates, vehicle type and vehicle color in JSON format like this:
{"bbox_2d": [x1, y1, x2, y2], "label": "vehicle", "type": "car/bus/truck/bicycle/motorcycle", "color": "vehicle_color"}'''
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",
        base_url=api_base_url
    )
    
    # Call API
    print("\nDetecting vehicles with attributes...")
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
    
    # Print summary with attributes
    type_counts = {}
    color_counts = {}
    
    for det in detections:
        vtype = det.get("type", "unknown")
        vcolor = det.get("color", "unknown")
        type_counts[vtype] = type_counts.get(vtype, 0) + 1
        color_counts[vcolor] = color_counts.get(vcolor, 0) + 1
    
    print(f"\nFound {len(detections)} vehicles")
    print("\nBy type:")
    for vtype, count in sorted(type_counts.items()):
        print(f"  - {vtype}: {count}")
    
    print("\nBy color:")
    for vcolor, count in sorted(color_counts.items()):
        print(f"  - {vcolor}: {count}")
    
    return detections, image, width, height


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect vehicles with type and color attributes')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--output', '-o', default='output_vehicles.jpg',
                       help='Output image path (default: output_vehicles.jpg)')
    parser.add_argument('--api-url', default=API_BASE_URL,
                       help=f'API base URL (default: {API_BASE_URL})')
    parser.add_argument('--model', default=MODEL_NAME,
                       help=f'Model name (default: {MODEL_NAME})')
    
    args = parser.parse_args()
    
    # Detect vehicles
    detections, image, width, height = detect_vehicles(
        args.image,
        args.api_url,
        args.model
    )
    
    # Draw and save
    plot_bounding_boxes(image, detections, args.output)
    
    print(f"\nDone! Open {args.output} to see the results.")


if __name__ == "__main__":
    main()
