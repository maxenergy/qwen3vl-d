# CLI Tool for AI Auto-Annotation

Command-line interface for managing the complete ML annotation workflow.

## Installation

After installing the package, the CLI tool will be available as `qwen3vl-annotate`:

```bash
pip install -e .
```

## Configuration

Set the backend API URL (defaults to http://localhost:8000):

```bash
export API_BASE_URL=http://your-backend-api:8000
```

Or use the `--api-url` flag with each command.

## Usage

### General Help

```bash
qwen3vl-annotate --help
```

### Projects

#### List all projects
```bash
qwen3vl-annotate projects list
qwen3vl-annotate projects list --page 2 --per-page 50
```

#### Show project details
```bash
qwen3vl-annotate projects show <project_id>
```

#### Create a new project
```bash
qwen3vl-annotate projects create --name "My Project" --description "Project description"

# With labels
qwen3vl-annotate projects create --name "Vehicle Detection" \
  --labels '[{"name":"car","color":"#ff0000"},{"name":"truck","color":"#00ff00"}]'
```

#### Update a project
```bash
qwen3vl-annotate projects update <project_id> --name "New Name" --status archived
```

#### Delete a project
```bash
qwen3vl-annotate projects delete <project_id>
```

#### Add labels to a project
```bash
qwen3vl-annotate projects add-label <project_id> --name "pedestrian" --color "#0000ff"
```

### Generation

#### List generation tasks
```bash
qwen3vl-annotate generation list <project_id>
```

#### Show generation task details
```bash
qwen3vl-annotate generation show <project_id> <task_id>
```

#### Create a generation task
```bash
qwen3vl-annotate generation create <project_id> \
  --name "Generate Cars" \
  --prompt "A photo of a car on a highway" \
  --count 100 \
  --model stable-diffusion-xl \
  --width 1024 \
  --height 1024
```

### Images

#### List images
```bash
qwen3vl-annotate images list <project_id>
qwen3vl-annotate images list <project_id> --review-status approved
```

#### Review an image
```bash
# Approve
qwen3vl-annotate images review <project_id> <image_id> --approve --notes "Good quality"

# Reject
qwen3vl-annotate images review <project_id> <image_id> --reject --notes "Blurry image"
```

### Annotation

#### List annotation tasks
```bash
qwen3vl-annotate annotation list <project_id>
```

#### Show annotation task details
```bash
qwen3vl-annotate annotation show <project_id> <task_id>
```

#### Create an annotation task
```bash
qwen3vl-annotate annotation create <project_id> \
  --name "Annotate Cars" \
  --description "Auto-annotate car images" \
  --image-ids "1,2,3,4,5" \
  --label-ids "1,2" \
  --confidence 0.5 \
  --model qwen3-vl-30b
```

#### Show annotation statistics
```bash
qwen3vl-annotate annotation stats <project_id>
```

### Datasets

#### List dataset versions
```bash
qwen3vl-annotate datasets list <project_id>
```

#### Show dataset details
```bash
qwen3vl-annotate datasets show <project_id> <dataset_id>
```

#### Create a dataset version
```bash
qwen3vl-annotate datasets create <project_id> \
  --version "v1.0.0" \
  --description "Initial dataset" \
  --train-ratio 0.7 \
  --val-ratio 0.2 \
  --test-ratio 0.1 \
  --export-formats "yolo,coco"
```

#### Export a dataset
```bash
qwen3vl-annotate datasets export <project_id> <dataset_id> --format yolo
qwen3vl-annotate datasets export <project_id> <dataset_id> --format coco
```

### Training

#### List training tasks
```bash
qwen3vl-annotate training list <project_id>
```

#### Show training task details
```bash
qwen3vl-annotate training show <project_id> <task_id>
```

#### Create a training task
```bash
qwen3vl-annotate training create <project_id> \
  --name "Train YOLOv8" \
  --dataset-id 1 \
  --yolo-version yolov8n \
  --epochs 100 \
  --batch-size 16 \
  --img-size 640 \
  --lr 0.01

# With additional hyperparameters
qwen3vl-annotate training create <project_id> \
  --name "Train YOLOv11" \
  --dataset-id 1 \
  --yolo-version yolov11m \
  --epochs 200 \
  --hyperparams '{"weight_decay": 0.0005, "momentum": 0.937}'
```

#### Stop a training task
```bash
qwen3vl-annotate training stop <project_id> <task_id>
```

#### List trained models
```bash
qwen3vl-annotate training models <project_id>
```

#### Show model details
```bash
qwen3vl-annotate training model-show <project_id> <model_id>
```

## Examples

### Complete Workflow

```bash
# 1. Create a project
qwen3vl-annotate projects create --name "Vehicle Detection" \
  --labels '[{"name":"car","color":"#ff0000"},{"name":"truck","color":"#00ff00"}]'
# Output: Created project: Vehicle Detection (ID: 1)

# 2. Generate images
qwen3vl-annotate generation create 1 \
  --name "Generate Vehicles" \
  --prompt "A photo of cars and trucks on a highway" \
  --count 100

# 3. Review and approve images
qwen3vl-annotate images list 1 --review-status pending
qwen3vl-annotate images review 1 1 --approve
qwen3vl-annotate images review 1 2 --approve

# 4. Create annotation task
qwen3vl-annotate annotation create 1 \
  --name "Auto Annotate" \
  --image-ids "1,2,3,4,5" \
  --label-ids "1,2" \
  --confidence 0.5

# 5. Check annotation statistics
qwen3vl-annotate annotation stats 1

# 6. Create dataset
qwen3vl-annotate datasets create 1 \
  --version "v1.0.0" \
  --train-ratio 0.7 \
  --val-ratio 0.2 \
  --test-ratio 0.1

# 7. Start training
qwen3vl-annotate training create 1 \
  --name "Train Model v1" \
  --dataset-id 1 \
  --yolo-version yolov8n \
  --epochs 100

# 8. Monitor training
qwen3vl-annotate training show 1 1

# 9. Export dataset
qwen3vl-annotate datasets export 1 1 --format yolo
```

## Tips

- Use `--help` with any command to see available options
- Set `API_BASE_URL` environment variable to avoid passing `--api-url` each time
- Use JSON format for complex parameters like labels and hyperparameters
- Commands support pagination with `--page` and `--per-page` options
- Status filters help narrow down results (e.g., `--status running`)
