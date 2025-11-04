#!/usr/bin/env python3
"""Demo of point-based detection features."""

from qwen3vl_d import Qwen3VLClient

# Initialize client
client = Qwen3VLClient(
    api_url="http://192.168.8.147:9292/v1",
    model_name="qwen3-vl-30b"
)

print("=" * 70)
print("POINT-BASED DETECTION DEMO")
print("=" * 70)

# Example 1: Simple point detection
print("\n1. Simple Point Detection (marking people with points)")
print("-" * 70)
detections, viz = client.detect_points(
    "test_images/samples/your_image.jpg",
    category="person",
    save_output="outputs/demo_points_people.jpg"
)
print(f"✓ Found {len(detections)} people")
print(f"✓ First person at: {detections[0]['point_2d']}")
print(f"✓ Saved visualization to: outputs/demo_points_people.jpg")

# Example 2: Detect different object with points
print("\n2. Detect Different Objects")
print("-" * 70)
face_detections = client.detect_points(
    "test_images/samples/your_image.jpg",
    category="face",
    save_output="outputs/demo_points_faces.jpg",
    visualize=True
)
print(f"✓ Found {len(face_detections)} faces")
print(f"✓ Saved visualization to: outputs/demo_points_faces.jpg")

# Example 3: Raw detections without visualization
print("\n3. Raw Detections (no visualization)")
print("-" * 70)
raw_detections = client.detect_points(
    "test_images/samples/your_image.jpg",
    category="person",
    visualize=False
)
print(f"✓ Received {len(raw_detections)} raw point detections")
print(f"✓ Each detection: {raw_detections[0].keys()}")

# Example 4: Point detection with attributes (commented - needs sports image)
print("\n4. Point Detection with Attributes")
print("-" * 70)
print("(Example for sports images with player attributes)")
print("Code:")
print("""
detections, viz = client.detect_points(
    "football.jpg",
    category="person",
    attributes={
        "role": "player/referee/unknown",
        "shirt_color": "color"
    },
    save_output="points_with_attributes.jpg"
)

for det in detections:
    print(f"{det['role']} wearing {det['shirt_color']} shirt at {det['point_2d']}")
""")

print("\n" + "=" * 70)
print("✅ All examples completed!")
print("=" * 70)
print(f"\nOutput files saved to: outputs/")
print("  - demo_points_people.jpg (people marked with points)")
print("  - demo_points_faces.jpg (faces marked with points)")
