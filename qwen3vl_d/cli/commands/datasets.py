"""Dataset management commands."""

import click
import json
from tabulate import tabulate
from ..api_client import APIClient


@click.group('datasets')
def datasets():
    """Manage dataset versions."""
    pass


@datasets.command('list')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.pass_context
def list_datasets(ctx, project_id: int, page: int):
    """List dataset versions."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_datasets(project_id, page=page)
        datasets = result.get('items', [])

        if not datasets:
            click.echo("No datasets found.")
            return

        headers = ['ID', 'Version', 'Status', 'Images', 'Annotations', 'Size (GB)', 'Created']
        rows = []
        for d in datasets:
            rows.append([
                d['id'],
                d['version'],
                d['status'],
                d.get('total_images', 0),
                d.get('total_annotations', 0),
                f"{d.get('size_gb', 0):.2f}",
                d['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@datasets.command('show')
@click.argument('project_id', type=int)
@click.argument('dataset_id', type=int)
@click.pass_context
def show_dataset(ctx, project_id: int, dataset_id: int):
    """Show dataset details."""
    client: APIClient = ctx.obj['client']

    try:
        dataset = client.get_dataset(project_id, dataset_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Dataset: {dataset['version']} (ID: {dataset['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {dataset['status']}")
        click.echo(f"Total Images: {dataset.get('total_images', 0)}")
        click.echo(f"Total Annotations: {dataset.get('total_annotations', 0)}")
        click.echo(f"Size: {dataset.get('size_gb', 0):.2f} GB")
        click.echo(f"Created: {dataset['created_at']}")

        if dataset.get('description'):
            click.echo(f"\nDescription: {dataset['description']}")

        if dataset.get('split_config'):
            split = dataset['split_config']
            click.echo(f"\nData Split:")
            click.echo(f"  Train: {split.get('train_ratio', 0):.0%}")
            click.echo(f"  Val: {split.get('val_ratio', 0):.0%}")
            click.echo(f"  Test: {split.get('test_ratio', 0):.0%}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@datasets.command('create')
@click.argument('project_id', type=int)
@click.option('--version', prompt=True, help='Dataset version (e.g., v1.0.0)')
@click.option('--description', default='', help='Dataset description')
@click.option('--train-ratio', default=0.7, help='Training set ratio (0-1)')
@click.option('--val-ratio', default=0.2, help='Validation set ratio (0-1)')
@click.option('--test-ratio', default=0.1, help='Test set ratio (0-1)')
@click.option('--export-formats', default='yolo,coco', help='Export formats (comma-separated)')
@click.pass_context
def create_dataset(ctx, project_id: int, version: str, description: str,
                  train_ratio: float, val_ratio: float, test_ratio: float,
                  export_formats: str):
    """Create a new dataset version."""
    client: APIClient = ctx.obj['client']

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        click.echo("Error: Split ratios must sum to 1.0", err=True)
        raise click.Abort()

    try:
        data = {
            'version': version,
            'description': description,
            'split_config': {
                'train_ratio': train_ratio,
                'val_ratio': val_ratio,
                'test_ratio': test_ratio
            },
            'export_formats': export_formats.split(',')
        }

        dataset = client.create_dataset(project_id, **data)
        click.echo(f"✓ Created dataset: {dataset['version']} (ID: {dataset['id']})")
        click.echo(f"Status: {dataset['status']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@datasets.command('export')
@click.argument('project_id', type=int)
@click.argument('dataset_id', type=int)
@click.option('--format', type=click.Choice(['yolo', 'coco']), default='yolo',
              help='Export format')
@click.pass_context
def export_dataset(ctx, project_id: int, dataset_id: int, format: str):
    """Export dataset."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.export_dataset(project_id, dataset_id, format=format)
        click.echo(f"✓ Dataset exported successfully")
        click.echo(f"Format: {format.upper()}")
        click.echo(f"Download URL: {result['download_url']}")
        click.echo(f"File Size: {result['file_size_mb']:.2f} MB")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
