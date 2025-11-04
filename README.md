# Qwen3-VL Object Detection Suite

A comprehensive collection of Python scripts for object detection using Qwen3-VL vision-language model via local OpenAI-compatible API.

## Features

- **Face Detection** - Detect and locate faces in images
- **Multi-Category Detection** - Detect multiple object categories simultaneously
- **Vehicle Detection** - Detect vehicles with type and color attributes
- **People Detection** - Detailed detection including body parts (heads, hands, glasses)
- **Point-Based Grounding** - Mark objects with point coordinates instead of bounding boxes
- **Description-Based Search** - Find specific objects using natural language descriptions

## Requirements

```bash
pip install openai pillow
```

## Configuration

All scripts connect to a local API endpoint by default. Edit the configuration in each script or use command-line arguments:

- **API URL**: `http://192.168.8.147:9292/v1` (default)
- **Model**: `qwen3-vl-30b` (default)

## Scripts Overview

### 1. detect_faces.py

Detect faces in images with bounding boxes.

**Usage:**
```bash
python detect_faces.py
```

**Default Settings:**
- Input: `your_image.jpg`
- Output: `output_faces.jpg`

**Code Example:**
```python
from detect_faces import detect_faces, draw_faces

faces, image, width, height = detect_faces("my_photo.jpg", "http://192.168.8.147:9292/v1")
draw_faces(faces, image, width, height, "result.jpg")
```

---

### 2. detect_objects.py

Detect multiple object categories in a single image.

**Usage:**
```bash
# Basic usage
python detect_objects.py image.jpg --categories "car,person,bicycle,dog"

# Specify output path
python detect_objects.py image.jpg -c "plate,cup,fork,spoon" -o dining_table.jpg

# Use custom API
python detect_objects.py image.jpg -c "tree,building,car" --api-url http://localhost:8000/v1
```

**Example Categories:**
- Vehicles: `car, bus, truck, bicycle, motorcycle`
- Animals: `dog, cat, bird, horse, cow`
- Food: `apple, banana, pizza, sandwich, cake`
- Household: `chair, table, tv, laptop, phone`
- People: `person, man, woman, child`

---

### 3. detect_vehicles.py

Detect vehicles with detailed attributes (type and color).

**Usage:**
```bash
# Basic usage
python detect_vehicles.py street_scene.jpg

# Custom output
python detect_vehicles.py parking_lot.jpg -o vehicles_detected.jpg

# Use custom API
python detect_vehicles.py traffic.jpg --api-url http://localhost:8000/v1
```

**Output Format:**
```json
{
  "bbox_2d": [x1, y1, x2, y2],
  "label": "vehicle",
  "type": "car",
  "color": "red"
}
```

**Detected Vehicle Types:**
- car
- bus
- truck
- bicycle
- motorcycle

---

### 4. detect_people.py

Detect people with optional body parts (heads, hands, glasses).

**Usage:**
```bash
# Detect people with body parts
python detect_people.py crowd.jpg

# Detect only people (no body parts)
python detect_people.py group_photo.jpg --no-parts

# Custom output
python detect_people.py event.jpg -o people_detected.jpg
```

**Detected Categories:**
- Full people: `person, man, woman`
- Body parts: `head, hand`
- Accessories: `glasses`

---

### 5. detect_with_points.py

Use point-based grounding to mark objects with coordinates instead of bounding boxes.

**Usage:**
```bash
# Basic point detection
python detect_with_points.py image.jpg --category "person"

# With attributes (e.g., players with roles and shirt colors)
python detect_with_points.py soccer.jpg -c "person" -a role="player/referee" shirt_color=color

# Detect cars
python detect_with_points.py parking.jpg -c "car" -o car_points.jpg
```

**Output Format:**
```json
{
  "point_2d": [x, y],
  "label": "person",
  "role": "player",
  "shirt_color": "red"
}
```

**Examples:**
```bash
# Football players with roles and shirt colors
python detect_with_points.py football.jpg -c "person" -a role="player/referee" shirt_color=color

# People with any custom attributes
python detect_with_points.py concert.jpg -c "person" -a position="standing/sitting"
```

---

### 6. detect_specific.py

Find specific objects using natural language descriptions.

**Usage:**
```bash
# Find with bounding box
python detect_specific.py image.jpg --description "the brown cake in the top right corner"

# Find with point
python detect_specific.py image.jpg -d "the red car on the left side" --points

# Custom output
python detect_specific.py image.jpg -d "the person wearing glasses" -o found.jpg
```

**Example Descriptions:**
```bash
# Objects by position
python detect_specific.py room.jpg -d "the lamp on the right side of the table"

# Objects by color and type
python detect_specific.py street.jpg -d "the blue sedan in the middle"

# Objects by unique features
python detect_specific.py crowd.jpg -d "the person wearing a red hat"

# Objects by relation
python detect_specific.py kitchen.jpg -d "the cup next to the coffee maker"
```

---

## Utils Module (utils.py)

Shared utilities for visualization and JSON parsing.

**Functions:**

### `parse_json_response(text)`
Parse JSON from model response, handling markdown fencing.

### `plot_bounding_boxes(image, detections, output_path=None)`
Draw bounding boxes with labels on image.

### `plot_points(image, detections, output_path=None)`
Draw point markers with labels on image.

### `get_font(size=14)`
Get appropriate font for the system.

**Example:**
```python
from utils import plot_bounding_boxes, parse_json_response
from PIL import Image

# Load image
image = Image.open("photo.jpg")

# Assume we have detections in JSON format
detections = [
    {"bbox_2d": [100, 200, 300, 400], "label": "car", "color": "red"},
    {"bbox_2d": [500, 150, 600, 350], "label": "person"}
]

# Plot and save
plot_bounding_boxes(image, detections, "output.jpg")
```

---

## Coordinate System

Qwen3-VL uses **normalized coordinates** ranging from **0 to 1000**.

### Bounding Boxes
Format: `[x1, y1, x2, y2]` where:
- `x1, y1`: Top-left corner (normalized 0-1000)
- `x2, y2`: Bottom-right corner (normalized 0-1000)

**Conversion to absolute pixels:**
```python
abs_x1 = int(bbox[0] / 1000 * image_width)
abs_y1 = int(bbox[1] / 1000 * image_height)
abs_x2 = int(bbox[2] / 1000 * image_width)
abs_y2 = int(bbox[3] / 1000 * image_height)
```

### Points
Format: `[x, y]` where both are normalized 0-1000.

**Conversion to absolute pixels:**
```python
abs_x = int(point[0] / 1000 * image_width)
abs_y = int(point[1] / 1000 * image_height)
```

---

## Examples

### Example 1: Detect Objects on a Dining Table
```bash
python detect_objects.py dining.jpg \
  --categories "plate,dish,cup,spoon,fork,wine bottle,bowl"
```

### Example 2: Analyze Traffic Scene
```bash
python detect_vehicles.py traffic.jpg
# Output includes vehicle types and colors
```

### Example 3: Find Specific Person in Crowd
```bash
python detect_specific.py crowd.jpg \
  --description "the person wearing a red jacket in the center"
```

### Example 4: Sports Analysis
```bash
python detect_with_points.py soccer.jpg \
  --category "person" \
  --attributes role="player/referee" shirt_color=color
```

### Example 5: Detect People in Group Photo
```bash
# With body parts
python detect_people.py group.jpg

# Without body parts
python detect_people.py group.jpg --no-parts
```

---

## Troubleshooting

### Error: "Invalid image_url.url value"
Make sure you're using base64 encoding. All scripts in this suite handle this automatically.

### Error: Connection refused
Ensure your local API server is running at the specified URL:
```bash
# Check if server is running
curl http://192.168.8.147:9292/v1/models
```

### Poor Detection Results
- Ensure good image quality
- Try adjusting the prompt/categories
- Some complex scenes may exceed the model's detection limits (40-50 objects per category)

### Font Issues on macOS/Linux
The utils module automatically tries multiple font paths. If you see font warnings, it will fall back to default fonts.

---

## API Response Format

All detection scripts expect JSON responses in one of these formats:

### Bounding Box Format
```json
[
  {
    "bbox_2d": [x1, y1, x2, y2],
    "label": "category_name",
    "attribute1": "value1",
    "attribute2": "value2"
  }
]
```

### Point Format
```json
[
  {
    "point_2d": [x, y],
    "label": "category_name",
    "attribute1": "value1"
  }
]
```

---

## Advanced Usage

### Custom Prompts
You can modify the prompts in each script to customize detection behavior:

```python
# In detect_objects.py, modify the prompt variable:
prompt = f'''Locate every instance that belongs to the following categories: {categories_str}. 
For each object, also identify if it's in motion or stationary.
Report bbox coordinates in JSON format.'''
```

### Batch Processing
Process multiple images:

```bash
#!/bin/bash
for img in images/*.jpg; do
    python detect_objects.py "$img" -c "car,person,bicycle" -o "results/$(basename $img)"
done
```

### Integration with Other Tools
```python
import json
from detect_vehicles import detect_vehicles

# Detect vehicles
detections, image, w, h = detect_vehicles("street.jpg")

# Export to JSON
with open("detections.json", "w") as f:
    json.dump(detections, f, indent=2)

# Process detections
for det in detections:
    if det["type"] == "car" and det["color"] == "red":
        print(f"Found red car at {det['bbox_2d']}")
```

---

## Performance Tips

1. **Use appropriate image sizes**: Very large images (>4K) may be slower
2. **Limit categories**: Detecting 5-10 categories is faster than 20+
3. **API optimization**: Ensure your local API server has sufficient resources
4. **Batch processing**: Process multiple images in parallel if needed

---

## License

This project uses the Qwen3-VL model. Please refer to the model's license for usage terms.

---

## Credits

Based on the Qwen3-VL spatial understanding capabilities from Alibaba Cloud's Qwen team.
