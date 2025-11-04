# qwen3vl-d - Qwen3-VL Object Detection Package

A Python package for object detection using Qwen3-VL vision-language model via local OpenAI-compatible API.

## Installation

### Local Development Installation

```bash
# Clone or navigate to the repository
cd qwen3-vl-face-detection

# Install in editable mode
pip install -e .
```

### From Requirements

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from qwen3vl_d import Qwen3VLClient

# Initialize client
client = Qwen3VLClient(
    api_url="http://192.168.8.147:9292/v1",
    model_name="qwen3-vl-30b"
)

# Detect faces
detections, image = client.detect_faces(
    "photo.jpg",
    save_output="faces_detected.jpg"
)
print(f"Found {len(detections)} faces")

# Detect multiple objects
detections, image = client.detect_objects(
    "image.jpg",
    categories=["car", "person", "bicycle"],
    save_output="objects_detected.jpg"
)

# Detect vehicles with attributes
detections, image = client.detect_vehicles(
    "street.jpg",
    save_output="vehicles_detected.jpg"
)
```

## API Reference

### Qwen3VLClient

Main client class for object detection.

#### Constructor

```python
client = Qwen3VLClient(
    api_url: str = "http://192.168.8.147:9292/v1",
    model_name: str = "qwen3-vl-30b",
    api_key: str = "not-needed"
)
```

**Parameters:**
- `api_url`: Base URL for the API endpoint
- `model_name`: Model name to use for detection
- `api_key`: API key (optional for local servers)

#### Methods

##### detect_faces()

Detect faces in an image.

```python
detections, image = client.detect_faces(
    image: Union[str, Image.Image],
    save_output: Optional[str] = None,
    visualize: bool = True
)
```

**Parameters:**
- `image`: Path to image file or PIL Image object
- `save_output`: Optional path to save visualization
- `visualize`: Whether to create visualization (default: True)

**Returns:**
- If `visualize=True`: Tuple of (detections list, visualized PIL Image)
- If `visualize=False`: List of detection dictionaries

**Detection Format:**
```python
{
    "bbox_2d": [x1, y1, x2, y2],  # Normalized 0-1000
    "label": "face"
}
```

##### detect_objects()

Detect multiple object categories.

```python
detections, image = client.detect_objects(
    image: Union[str, Image.Image],
    categories: Union[List[str], str],
    save_output: Optional[str] = None,
    visualize: bool = True
)
```

**Parameters:**
- `image`: Path to image file or PIL Image object
- `categories`: List of categories or comma-separated string
- `save_output`: Optional path to save visualization
- `visualize`: Whether to create visualization (default: True)

**Example Categories:**
- Vehicles: `"car, bus, truck, bicycle, motorcycle"`
- Animals: `"dog, cat, bird, horse, cow"`
- Food: `"apple, banana, pizza, sandwich"`
- Household: `"chair, table, tv, laptop, phone"`

##### detect_vehicles()

Detect vehicles with type and color attributes.

```python
detections, image = client.detect_vehicles(
    image: Union[str, Image.Image],
    save_output: Optional[str] = None,
    visualize: bool = True
)
```

**Detection Format:**
```python
{
    "bbox_2d": [x1, y1, x2, y2],
    "label": "vehicle",
    "type": "car",  # car, bus, truck, bicycle, motorcycle
    "color": "red"
}
```

## Advanced Usage

### Working with PIL Images

```python
from PIL import Image
from qwen3vl_d import Qwen3VLClient

# Open image with PIL
image = Image.open("photo.jpg")

# Detect faces
client = Qwen3VLClient()
detections, viz_image = client.detect_faces(image)

# Save or display
viz_image.save("result.jpg")
viz_image.show()
```

### Getting Raw Detections

```python
# Get detections without visualization
detections = client.detect_faces(
    "photo.jpg",
    visualize=False
)

# Process detections
for det in detections:
    print(f"Face at {det['bbox_2d']}")
```

### Custom Visualization

```python
from qwen3vl_d import plot_bounding_boxes
from PIL import Image

# Get raw detections
detections = client.detect_objects(
    "image.jpg",
    categories=["car", "person"],
    visualize=False
)

# Custom visualization
image = Image.open("image.jpg")
viz_image = plot_bounding_boxes(image, detections, "custom_output.jpg")
```

### Batch Processing

```python
import os
from qwen3vl_d import Qwen3VLClient

client = Qwen3VLClient()

# Process multiple images
image_dir = "images/"
output_dir = "results/"
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(image_dir):
    if filename.endswith(('.jpg', '.png')):
        input_path = os.path.join(image_dir, filename)
        output_path = os.path.join(output_dir, f"detected_{filename}")
        
        detections, _ = client.detect_faces(
            input_path,
            save_output=output_path
        )
        print(f"{filename}: {len(detections)} faces detected")
```

## Coordination System

Qwen3-VL uses **normalized coordinates** from **0 to 1000**.

### Converting to Absolute Pixels

```python
from PIL import Image

image = Image.open("photo.jpg")
width, height = image.size

# Get detection
detection = detections[0]
bbox = detection["bbox_2d"]  # [x1, y1, x2, y2]

# Convert to absolute pixels
abs_x1 = int(bbox[0] / 1000 * width)
abs_y1 = int(bbox[1] / 1000 * height)
abs_x2 = int(bbox[2] / 1000 * width)
abs_y2 = int(bbox[3] / 1000 * height)
```

## Project Structure

```
qwen3-vl-face-detection/
├── qwen3vl_d/              # Main package
│   ├── __init__.py
│   ├── client.py           # Qwen3VLClient
│   ├── visualization.py    # Plotting utilities
│   └── detectors/
│       ├── __init__.py
│       ├── base.py         # BaseDetector
│       ├── faces.py        # FaceDetector
│       ├── objects.py      # ObjectDetector
│       └── vehicles.py     # VehicleDetector
├── scripts/                # CLI scripts (original)
│   ├── detect_faces.py
│   ├── detect_objects.py
│   └── ...
├── examples/               # Usage examples
│   └── basic_usage.py
├── setup.py               # Package setup
├── pyproject.toml         # Modern packaging
└── requirements.txt       # Dependencies
```

## CLI Scripts (Legacy)

The original CLI scripts are still available in the `scripts/` folder:

```bash
# Face detection
python scripts/detect_faces.py

# Multi-category detection
python scripts/detect_objects.py image.jpg --categories "car,person,bicycle"

# Vehicle detection
python scripts/detect_vehicles.py street.jpg

# And more...
```

## Requirements

- Python >= 3.8
- openai >= 1.0.0
- pillow >= 9.0.0

## License

MIT License

## Credits

Based on the Qwen3-VL spatial understanding capabilities from Alibaba Cloud's Qwen team.
