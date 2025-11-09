"""Annotation management commands."""

import click
import json
from tabulate import tabulate
from ..api_client import APIClient


@click.group('annotation')
def annotation():
    """Manage annotation tasks."""
    pass


@annotation.command('list')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.option('--status', help='Filter by status')
@click.pass_context
def list_tasks(ctx, project_id: int, page: int, status: str):
    """List annotation tasks."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_annotation_tasks(project_id, page=page)
        tasks = result.get('items', [])

        if not tasks:
            click.echo("No annotation tasks found.")
            return

        headers = ['ID', 'Name', 'Status', 'Progress', 'Annotations', 'Created']
        rows = []
        for t in tasks:
            rows.append([
                t['id'],
                t['name'][:30],
                t['status'],
                f"{t.get('progress', 0)}%",
                f"{t.get('annotated_images', 0)}/{t.get('total_images', 0)} images, {t.get('total_annotations', 0)} annotations",
                t['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@annotation.command('show')
@click.argument('project_id', type=int)
@click.argument('task_id', type=int)
@click.pass_context
def show_task(ctx, project_id: int, task_id: int):
    """Show annotation task details."""
    client: APIClient = ctx.obj['client']

    try:
        task = client.get_annotation_task(project_id, task_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Annotation Task: {task['name']} (ID: {task['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {task['status']}")
        click.echo(f"Progress: {task.get('progress', 0)}%")
        click.echo(f"Images: {task.get('annotated_images', 0)} / {task.get('total_images', 0)}")
        click.echo(f"Total Annotations: {task.get('total_annotations', 0)}")
        click.echo(f"Confidence Threshold: {task.get('confidence_threshold', 0.5)}")
        click.echo(f"Created: {task['created_at']}")

        if task.get('description'):
            click.echo(f"\nDescription: {task['description']}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@annotation.command('create')
@click.argument('project_id', type=int)
@click.option('--name', prompt=True, help='Task name')
@click.option('--description', default='', help='Task description')
@click.option('--image-ids', required=True, help='Comma-separated image IDs')
@click.option('--label-ids', required=True, help='Comma-separated label IDs')
@click.option('--confidence', default=0.5, help='Confidence threshold (0-1)')
@click.option('--model', default='qwen3-vl-30b', help='Model to use')
@click.pass_context
def create_task(ctx, project_id: int, name: str, description: str,
                image_ids: str, label_ids: str, confidence: float, model: str):
    """Create a new annotation task."""
    client: APIClient = ctx.obj['client']

    try:
        data = {
            'name': name,
            'description': description,
            'image_ids': [int(x.strip()) for x in image_ids.split(',')],
            'label_ids': [int(x.strip()) for x in label_ids.split(',')],
            'confidence_threshold': confidence,
            'model': model
        }

        task = client.create_annotation_task(project_id, **data)
        click.echo(f"✓ Created annotation task: {task['name']} (ID: {task['id']})")
        click.echo(f"Status: {task['status']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@annotation.command('stats')
@click.argument('project_id', type=int)
@click.pass_context
def show_statistics(ctx, project_id: int):
    """Show annotation statistics."""
    client: APIClient = ctx.obj['client']

    try:
        stats = client.get_annotation_statistics(project_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Annotation Statistics for Project {project_id}")
        click.echo(f"{'='*60}")
        click.echo(f"Total Annotations: {stats['total_annotations']}")
        click.echo(f"Verified: {stats['verified_count']}")
        click.echo(f"Average Confidence: {stats['avg_confidence']:.2%}")

        if stats.get('by_label'):
            click.echo(f"\nBy Label:")
            for label, count in stats['by_label'].items():
                click.echo(f"  {label}: {count}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
