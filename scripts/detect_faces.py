#!/usr/bin/env python3
"""
Face detection using Qwen3-VL via local OpenAI-compatible API
"""

import os
import json
import base64
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# Configuration
API_BASE_URL = "http://192.168.8.147:9292/v1"  # Adjust to your local API endpoint
IMAGE_PATH = "your_image.jpg"  # Path to your image

def detect_faces(image_path, api_base_url):
    """Detect faces in image using Qwen3-VL"""
    
    # Load image
    image = Image.open(image_path)
    width, height = image.size
    print(f"Image size: {width}x{height}")
    
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key="not-needed",  # Local API typically doesn't need real key
        base_url=api_base_url
    )
    
    # Prepare prompt
    prompt = '''Locate every face in this image. For each face, report bbox coordinates in JSON format like this:
{"bbox_2d": [x1, y1, x2, y2], "label": "face"}'''
    
    # Call API
    print("Detecting faces...")
    completion = client.chat.completions.create(
        model="qwen3-vl-30b",  # Adjust model name if needed
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
    # Remove markdown fencing if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    
    faces = json.loads(response_text.strip())
    print(f"Found {len(faces)} face(s)")
    
    return faces, image, width, height


def draw_faces(faces, image, width, height, output_path="output_faces.jpg"):
    """Draw bounding boxes on detected faces"""
    
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    colors = ['red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'cyan']
    
    for i, face in enumerate(faces):
        # Convert normalized coords (0-1000) to absolute
        x1 = int(face["bbox_2d"][0] / 1000 * width)
        y1 = int(face["bbox_2d"][1] / 1000 * height)
        x2 = int(face["bbox_2d"][2] / 1000 * width)
        y2 = int(face["bbox_2d"][3] / 1000 * height)
        
        # Ensure correct order
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        color = colors[i % len(colors)]
        
        # Draw bbox
        draw.rectangle(((x1, y1), (x2, y2)), outline=color, width=3)
        
        # Draw label
        label = face.get("label", f"face_{i+1}")
        draw.text((x1 + 5, y1 + 5), label, fill=color, font=font)
        
        print(f"Face {i+1}: [{x1}, {y1}, {x2}, {y2}]")
    
    # Save result
    image.save(output_path)
    print(f"\nSaved result to: {output_path}")
    
    return image


def main():
    # Detect faces
    faces, image, width, height = detect_faces(IMAGE_PATH, API_BASE_URL)
    
    # Draw and save
    draw_faces(faces, image, width, height)
    
    # Optionally display
    # image.show()


if __name__ == "__main__":
    main()
