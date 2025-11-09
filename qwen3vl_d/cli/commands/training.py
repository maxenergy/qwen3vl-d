"""Training management commands."""

import click
import json
from tabulate import tabulate
from ..api_client import APIClient


@click.group('training')
def training():
    """Manage training tasks and models."""
    pass


@training.command('list')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.option('--status', help='Filter by status')
@click.pass_context
def list_tasks(ctx, project_id: int, page: int, status: str):
    """List training tasks."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_training_tasks(project_id, page=page)
        tasks = result.get('items', [])

        if not tasks:
            click.echo("No training tasks found.")
            return

        headers = ['ID', 'Name', 'Status', 'Progress', 'mAP@50-95', 'Epoch', 'Created']
        rows = []
        for t in tasks:
            current_metrics = t.get('current_metrics', {})
            rows.append([
                t['id'],
                t['name'][:30],
                t['status'],
                f"{t.get('progress', 0)}%",
                f"{current_metrics.get('map50_95', 0):.3f}" if current_metrics.get('map50_95') else 'N/A',
                f"{t.get('current_epoch', 0)}/{t.get('total_epochs', 0)}",
                t['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@training.command('show')
@click.argument('project_id', type=int)
@click.argument('task_id', type=int)
@click.pass_context
def show_task(ctx, project_id: int, task_id: int):
    """Show training task details."""
    client: APIClient = ctx.obj['client']

    try:
        task = client.get_training_task(project_id, task_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Training Task: {task['name']} (ID: {task['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {task['status']}")
        click.echo(f"Progress: {task.get('progress', 0)}%")
        click.echo(f"Epoch: {task.get('current_epoch', 0)} / {task.get('total_epochs', 0)}")
        click.echo(f"Model: {task.get('yolo_version', 'N/A')}")
        click.echo(f"Created: {task['created_at']}")

        current = task.get('current_metrics', {})
        if current:
            click.echo(f"\nCurrent Metrics:")
            click.echo(f"  Train Loss: {current.get('train_loss', 0):.4f}")
            click.echo(f"  Val Loss: {current.get('val_loss', 0):.4f}")
            click.echo(f"  mAP@50: {current.get('map50', 0):.4f}")
            click.echo(f"  mAP@50-95: {current.get('map50_95', 0):.4f}")
            click.echo(f"  Precision: {current.get('precision', 0):.4f}")
            click.echo(f"  Recall: {current.get('recall', 0):.4f}")

        best = task.get('best_metrics', {})
        if best:
            click.echo(f"\nBest Metrics:")
            click.echo(f"  mAP@50: {best.get('map50', 0):.4f}")
            click.echo(f"  mAP@50-95: {best.get('map50_95', 0):.4f}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@training.command('create')
@click.argument('project_id', type=int)
@click.option('--name', prompt=True, help='Task name')
@click.option('--dataset-id', required=True, type=int, help='Dataset version ID')
@click.option('--yolo-version', default='yolov8n', help='YOLO version (e.g., yolov8n, yolov11m)')
@click.option('--epochs', default=100, help='Number of epochs')
@click.option('--batch-size', default=16, help='Batch size')
@click.option('--img-size', default=640, help='Image size')
@click.option('--lr', default=0.01, help='Learning rate')
@click.option('--hyperparams', help='Additional hyperparameters as JSON')
@click.pass_context
def create_task(ctx, project_id: int, name: str, dataset_id: int,
                yolo_version: str, epochs: int, batch_size: int,
                img_size: int, lr: float, hyperparams: str):
    """Create a new training task."""
    client: APIClient = ctx.obj['client']

    try:
        data = {
            'name': name,
            'dataset_id': dataset_id,
            'yolo_version': yolo_version,
            'hyperparameters': {
                'epochs': epochs,
                'batch': batch_size,
                'imgsz': img_size,
                'lr0': lr
            }
        }

        if hyperparams:
            extra = json.loads(hyperparams)
            data['hyperparameters'].update(extra)

        task = client.create_training_task(project_id, **data)
        click.echo(f"✓ Created training task: {task['name']} (ID: {task['id']})")
        click.echo(f"Status: {task['status']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@training.command('stop')
@click.argument('project_id', type=int)
@click.argument('task_id', type=int)
@click.confirmation_option(prompt='Are you sure you want to stop this training task?')
@click.pass_context
def stop_task(ctx, project_id: int, task_id: int):
    """Stop a running training task."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.stop_training_task(project_id, task_id)
        click.echo(f"✓ Training task {task_id} stopped")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@training.command('models')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.pass_context
def list_models(ctx, project_id: int, page: int):
    """List trained models."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_models(project_id, page=page)
        models = result.get('items', [])

        if not models:
            click.echo("No models found.")
            return

        headers = ['ID', 'Name', 'Version', 'mAP@50-95', 'Size (MB)', 'Created']
        rows = []
        for m in models:
            rows.append([
                m['id'],
                m['name'][:30],
                m['version'],
                f"{m.get('map50_95', 0):.3f}",
                f"{m.get('size_mb', 0):.1f}",
                m['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@training.command('model-show')
@click.argument('project_id', type=int)
@click.argument('model_id', type=int)
@click.pass_context
def show_model(ctx, project_id: int, model_id: int):
    """Show model details."""
    client: APIClient = ctx.obj['client']

    try:
        model = client.get_model(project_id, model_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Model: {model['name']} (ID: {model['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Version: {model['version']}")
        click.echo(f"YOLO Version: {model.get('yolo_version', 'N/A')}")
        click.echo(f"Size: {model.get('size_mb', 0):.2f} MB")
        click.echo(f"Created: {model['created_at']}")

        metrics = model.get('metrics', {})
        if metrics:
            click.echo(f"\nMetrics:")
            click.echo(f"  mAP@50: {metrics.get('map50', 0):.4f}")
            click.echo(f"  mAP@50-95: {metrics.get('map50_95', 0):.4f}")
            click.echo(f"  Precision: {metrics.get('precision', 0):.4f}")
            click.echo(f"  Recall: {metrics.get('recall', 0):.4f}")

        if model.get('model_path'):
            click.echo(f"\nModel Path: {model['model_path']}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
