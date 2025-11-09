"""Image generation commands."""

import click
import json
from tabulate import tabulate
from ..api_client import APIClient


@click.group('generation')
def generation():
    """Manage image generation tasks."""
    pass


@generation.command('list')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.option('--status', help='Filter by status')
@click.pass_context
def list_tasks(ctx, project_id: int, page: int, status: str):
    """List generation tasks."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_generation_tasks(project_id, page=page)
        tasks = result.get('items', [])

        if not tasks:
            click.echo("No generation tasks found.")
            return

        headers = ['ID', 'Name', 'Status', 'Progress', 'Images', 'Model', 'Created']
        rows = []
        for t in tasks:
            rows.append([
                t['id'],
                t['name'][:30],
                t['status'],
                f"{t.get('progress', 0)}%",
                f"{t.get('generated_count', 0)}/{t.get('total_count', 0)}",
                t.get('model', 'N/A')[:20],
                t['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@generation.command('show')
@click.argument('project_id', type=int)
@click.argument('task_id', type=int)
@click.pass_context
def show_task(ctx, project_id: int, task_id: int):
    """Show generation task details."""
    client: APIClient = ctx.obj['client']

    try:
        task = client.get_generation_task(project_id, task_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Generation Task: {task['name']} (ID: {task['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {task['status']}")
        click.echo(f"Progress: {task.get('progress', 0)}%")
        click.echo(f"Images: {task.get('generated_count', 0)} / {task.get('total_count', 0)}")
        click.echo(f"Model: {task.get('model', 'N/A')}")
        click.echo(f"Created: {task['created_at']}")

        if task.get('prompt'):
            click.echo(f"\nPrompt: {task['prompt']}")

        if task.get('error_message'):
            click.echo(f"\nError: {task['error_message']}")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@generation.command('create')
@click.argument('project_id', type=int)
@click.option('--name', prompt=True, help='Task name')
@click.option('--prompt', prompt=True, help='Generation prompt')
@click.option('--count', default=10, help='Number of images to generate')
@click.option('--model', default='stable-diffusion-xl', help='Model to use')
@click.option('--width', default=1024, help='Image width')
@click.option('--height', default=1024, help='Image height')
@click.option('--config', help='Additional config as JSON')
@click.pass_context
def create_task(ctx, project_id: int, name: str, prompt: str, count: int,
                model: str, width: int, height: int, config: str):
    """Create a new generation task."""
    client: APIClient = ctx.obj['client']

    try:
        data = {
            'name': name,
            'prompt': prompt,
            'count': count,
            'model': model,
            'width': width,
            'height': height
        }

        if config:
            data['config'] = json.loads(config)

        task = client.create_generation_task(project_id, **data)
        click.echo(f"✓ Created generation task: {task['name']} (ID: {task['id']})")
        click.echo(f"Status: {task['status']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
