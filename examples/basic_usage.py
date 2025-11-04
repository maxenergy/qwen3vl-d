"""Basic usage example for qwen3vl-d package."""

from qwen3vl_d import Qwen3VLClient

# Initialize the client with your API connection details
client = Qwen3VLClient(
    api_url="http://192.168.8.147:9292/v1",
    model_name="qwen3-vl-30b",
    api_key="not-needed"  # Optional for local servers
)

# Example 1: Detect faces
print("Example 1: Detecting faces...")
face_detections, face_image = client.detect_faces(
    "test_images/samples/your_image.jpg",
    save_output="outputs/output_faces_pkg.jpg"
)
print(f"Found {len(face_detections)} faces")

# Example 2: Detect multiple object categories
print("\nExample 2: Detecting multiple objects...")
object_detections, object_image = client.detect_objects(
    "test_images/samples/your_image.jpg",
    categories=["person", "face", "head"],
    save_output="outputs/output_objects_pkg.jpg"
)
print(f"Found {len(object_detections)} objects")

# Count by category
category_counts = {}
for det in object_detections:
    label = det.get("label", "unknown")
    category_counts[label] = category_counts.get(label, 0) + 1

print("Breakdown by category:")
for category, count in sorted(category_counts.items()):
    print(f"  - {category}: {count}")

# Example 3: Detect vehicles (if you have a street image)
# print("\nExample 3: Detecting vehicles...")
# vehicle_detections, vehicle_image = client.detect_vehicles(
#     "street_scene.jpg",
#     save_output="output_vehicles_pkg.jpg"
# )
# print(f"Found {len(vehicle_detections)} vehicles")

# Example 4: Get raw detections without visualization
print("\nExample 4: Getting raw detections...")
raw_detections = client.detect_faces(
    "test_images/samples/your_image.jpg",
    visualize=False
)
print(f"Raw detection data (first one): {raw_detections[0]}")

print("\nAll examples completed!")
