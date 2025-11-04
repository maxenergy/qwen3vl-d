#!/usr/bin/env python3
"""Test script for point-based detection."""

from qwen3vl_d import Qwen3VLClient

# Initialize client
client = Qwen3VLClient(
    api_url="http://192.168.8.147:9292/v1",
    model_name="qwen3-vl-30b"
)

print("Testing point-based detection...\n")

# Test 1: Simple point detection
print("Test 1: Simple point detection (people)")
detections, viz = client.detect_points(
    "test_images/samples/your_image.jpg",
    category="person",
    save_output="outputs/points_simple.jpg"
)
print(f"Found {len(detections)} people")
print(f"First detection: {detections[0]}\n")

# Test 2: Point detection with attributes (if we had a sports image)
# print("Test 2: Point detection with attributes (football players)")
# detections, viz = client.detect_points(
#     "test_images/sports/sports1.jpg",
#     category="person",
#     attributes={"role": "player/referee", "shirt_color": "color"},
#     save_output="outputs/points_attributes.jpg"
# )
# print(f"Found {len(detections)} people")
# for i, det in enumerate(detections[:3]):  # Show first 3
#     print(f"  {i+1}. {det.get('role', 'unknown')} in {det.get('shirt_color', 'unknown')} shirt")

# Test 3: Raw detections without visualization
print("\nTest 3: Raw detections (no visualization)")
raw_detections = client.detect_points(
    "test_images/samples/your_image.jpg",
    category="person",
    visualize=False
)
print(f"Got {len(raw_detections)} raw detections")
print(f"Type: {type(raw_detections)}")

print("\n✅ All point detection tests completed!")
