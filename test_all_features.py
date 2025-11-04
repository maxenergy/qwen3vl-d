#!/usr/bin/env python3
"""Comprehensive test suite for qwen3vl-d package."""

import os
from datetime import datetime
from PIL import Image
from qwen3vl_d import Qwen3VLClient

# Initialize client
client = Qwen3VLClient(
    api_url="http://192.168.8.147:9292/v1",
    model_name="qwen3-vl-30b"
)

# Create output directory
output_dir = "test_results"
os.makedirs(output_dir, exist_ok=True)

# Test results storage
results = []

def log_test(test_name, status, details=""):
    """Log test result."""
    results.append({
        "test": test_name,
        "status": status,
        "details": details
    })
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"{status_symbol} {test_name}: {details}")

print("=" * 80)
print("COMPREHENSIVE TEST SUITE FOR qwen3vl-d")
print("=" * 80)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# TEST SUITE 1: Vehicle Detection on Street Scenes
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 1: Vehicle Detection on Street Scenes")
print("="*80)

street_scenes = ["test_images/street_scenes/street-scene1.jpg", "test_images/street_scenes/street-scene2.jpg", "test_images/street_scenes/street-scene3.jpg"]

for i, image_file in enumerate(street_scenes, 1):
    if not os.path.exists(image_file):
        log_test(f"Vehicle Detection - {image_file}", "SKIP", "Image not found")
        continue
    
    try:
        print(f"\nTesting {image_file}...")
        detections, viz_image = client.detect_vehicles(
            image_file,
            save_output=f"{output_dir}/vehicles_{i}.jpg"
        )
        
        # Count by type and color
        types = {}
        colors = {}
        for det in detections:
            vtype = det.get("type", "unknown")
            vcolor = det.get("color", "unknown")
            types[vtype] = types.get(vtype, 0) + 1
            colors[vcolor] = colors.get(vcolor, 0) + 1
        
        details = f"{len(detections)} vehicles | Types: {types} | Colors: {colors}"
        log_test(f"Vehicle Detection - {image_file}", "PASS", details)
        
    except Exception as e:
        log_test(f"Vehicle Detection - {image_file}", "FAIL", str(e))

# ============================================================================
# TEST SUITE 2: People Detection on Crowd Images
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 2: People Detection on Crowd Images")
print("="*80)

crowd_images = ["test_images/crowds/crowd1.jpg", "test_images/crowds/crowd2.jpg", "test_images/crowds/crowd3.jpg"]

for i, image_file in enumerate(crowd_images, 1):
    if not os.path.exists(image_file):
        log_test(f"People Detection - {image_file}", "SKIP", "Image not found")
        continue
    
    try:
        print(f"\nTesting {image_file}...")
        detections, viz_image = client.detect_objects(
            image_file,
            categories=["person", "man", "woman", "head", "hand", "glasses"],
            save_output=f"{output_dir}/crowd_{i}.jpg"
        )
        
        # Count by category
        category_counts = {}
        for det in detections:
            label = det.get("label", "unknown")
            category_counts[label] = category_counts.get(label, 0) + 1
        
        details = f"{len(detections)} detections | {category_counts}"
        log_test(f"People Detection - {image_file}", "PASS", details)
        
    except Exception as e:
        log_test(f"People Detection - {image_file}", "FAIL", str(e))

# ============================================================================
# TEST SUITE 3: Object Detection on Interior Rooms
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 3: Object Detection on Interior Rooms")
print("="*80)

interior_images = [
    "test_images/interiors/interior-room1.jpg",
    "test_images/interiors/interior-room2.jpg",
    "test_images/interiors/interior-room3.jpg",
    "test_images/interiors/interior-room4.jpg"
]

for i, image_file in enumerate(interior_images, 1):
    if not os.path.exists(image_file):
        log_test(f"Interior Detection - {image_file}", "SKIP", "Image not found")
        continue
    
    try:
        print(f"\nTesting {image_file}...")
        detections, viz_image = client.detect_objects(
            image_file,
            categories=["chair", "table", "sofa", "bed", "lamp", "tv", "plant", "window", "door"],
            save_output=f"{output_dir}/interior_{i}.jpg"
        )
        
        # Count by category
        category_counts = {}
        for det in detections:
            label = det.get("label", "unknown")
            category_counts[label] = category_counts.get(label, 0) + 1
        
        details = f"{len(detections)} objects | {category_counts}"
        log_test(f"Interior Detection - {image_file}", "PASS", details)
        
    except Exception as e:
        log_test(f"Interior Detection - {image_file}", "FAIL", str(e))

# ============================================================================
# TEST SUITE 4: Different Image Formats
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 4: Different Image Formats (.jpg, .webp, .jpeg)")
print("="*80)

format_tests = [
    ("test_images/sports/sports1.jpg", "JPG format"),
    ("test_images/sports/sports2.webp", "WEBP format"),
    ("test_images/sports/sports3.jpeg", "JPEG format"),
]

for image_file, format_desc in format_tests:
    if not os.path.exists(image_file):
        log_test(f"Format Test - {format_desc}", "SKIP", "Image not found")
        continue
    
    try:
        print(f"\nTesting {format_desc} ({image_file})...")
        detections, viz_image = client.detect_objects(
            image_file,
            categories=["person", "ball", "player"],
            save_output=f"{output_dir}/format_{image_file.split('.')[0]}.jpg"
        )
        
        details = f"{len(detections)} detections"
        log_test(f"Format Test - {format_desc}", "PASS", details)
        
    except Exception as e:
        log_test(f"Format Test - {format_desc}", "FAIL", str(e))

# ============================================================================
# TEST SUITE 5: PIL Image Input (not just file paths)
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 5: PIL Image Object Input")
print("="*80)

if os.path.exists("test_images/samples/your_image.jpg"):
    try:
        print("\nTesting PIL Image object input...")
        
        # Load image with PIL
        pil_image = Image.open("test_images/samples/your_image.jpg")
        
        # Detect faces using PIL Image
        detections, viz_image = client.detect_faces(
            pil_image,
            save_output=f"{output_dir}/pil_image_test.jpg"
        )
        
        details = f"{len(detections)} faces detected from PIL Image object"
        log_test("PIL Image Input", "PASS", details)
        
    except Exception as e:
        log_test("PIL Image Input", "FAIL", str(e))
else:
    log_test("PIL Image Input", "SKIP", "Test image not found")

# ============================================================================
# TEST SUITE 6: Raw Detections (visualize=False)
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 6: Raw Detections (No Visualization)")
print("="*80)

if os.path.exists("test_images/samples/your_image.jpg"):
    try:
        print("\nTesting raw detections (visualize=False)...")
        
        # Get raw detections without visualization
        detections = client.detect_faces("test_images/samples/your_image.jpg", visualize=False)
        
        # Verify we got a list of dicts (not tuple)
        assert isinstance(detections, list), "Should return list, not tuple"
        assert len(detections) > 0, "Should have detections"
        assert "bbox_2d" in detections[0], "Should have bbox_2d"
        
        details = f"{len(detections)} detections returned as raw data (no tuple)"
        log_test("Raw Detections", "PASS", details)
        
    except Exception as e:
        log_test("Raw Detections", "FAIL", str(e))
else:
    log_test("Raw Detections", "SKIP", "Test image not found")

# ============================================================================
# TEST SUITE 7: Multi-format sports detection
# ============================================================================
print("\n" + "="*80)
print("TEST SUITE 7: Sports Object Detection (All Formats)")
print("="*80)

sports_images = ["test_images/sports/sports1.jpg", "test_images/sports/sports2.webp", "test_images/sports/sports3.jpeg", "test_images/sports/sports4.jpeg"]

for i, image_file in enumerate(sports_images, 1):
    if not os.path.exists(image_file):
        log_test(f"Sports Detection - {image_file}", "SKIP", "Image not found")
        continue
    
    try:
        print(f"\nTesting {image_file}...")
        detections, viz_image = client.detect_objects(
            image_file,
            categories=["person", "player", "ball", "goal", "referee"],
            save_output=f"{output_dir}/sports_{i}.jpg"
        )
        
        category_counts = {}
        for det in detections:
            label = det.get("label", "unknown")
            category_counts[label] = category_counts.get(label, 0) + 1
        
        details = f"{len(detections)} objects | {category_counts}"
        log_test(f"Sports Detection - {image_file}", "PASS", details)
        
    except Exception as e:
        log_test(f"Sports Detection - {image_file}", "FAIL", str(e))

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
skipped = sum(1 for r in results if r["status"] == "SKIP")
total = len(results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⊘ Skipped: {skipped}")
print(f"\nSuccess Rate: {(passed/total*100):.1f}%")

# Save detailed report
report_file = f"{output_dir}/test_report.txt"
with open(report_file, "w") as f:
    f.write("="*80 + "\n")
    f.write("COMPREHENSIVE TEST REPORT FOR qwen3vl-d\n")
    f.write("="*80 + "\n")
    f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write(f"Total Tests: {total}\n")
    f.write(f"Passed: {passed}\n")
    f.write(f"Failed: {failed}\n")
    f.write(f"Skipped: {skipped}\n")
    f.write(f"Success Rate: {(passed/total*100):.1f}%\n\n")
    
    f.write("="*80 + "\n")
    f.write("DETAILED RESULTS\n")
    f.write("="*80 + "\n\n")
    
    for result in results:
        status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⊘"
        f.write(f"{status_symbol} {result['test']}\n")
        f.write(f"   Status: {result['status']}\n")
        f.write(f"   Details: {result['details']}\n\n")

print(f"\n📄 Detailed report saved to: {report_file}")
print(f"📁 All output images saved to: {output_dir}/")
print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
