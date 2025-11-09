"""Project management commands."""

import click
import json
from tabulate import tabulate
from ..api_client import APIClient


@click.group('projects')
def projects():
    """Manage projects."""
    pass


@projects.command('list')
@click.option('--page', default=1, help='Page number')
@click.option('--per-page', default=20, help='Items per page')
@click.pass_context
def list_projects(ctx, page: int, per_page: int):
    """List all projects."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.list_projects(page=page, per_page=per_page)
        projects = result.get('items', [])

        if not projects:
            click.echo("No projects found.")
            return

        # Prepare table data
        headers = ['ID', 'Name', 'Status', 'Images', 'Annotations', 'Labels', 'Created']
        rows = []
        for p in projects:
            rows.append([
                p['id'],
                p['name'][:40] if len(p['name']) > 40 else p['name'],
                p['status'],
                p.get('image_count', 0),
                p.get('annotation_count', 0),
                p.get('label_count', 0),
                p['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        click.echo(f"\nPage {result.get('page', 1)} of {result.get('total', 0) // per_page + 1}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command('show')
@click.argument('project_id', type=int)
@click.pass_context
def show_project(ctx, project_id: int):
    """Show project details."""
    client: APIClient = ctx.obj['client']

    try:
        project = client.get_project(project_id)

        click.echo(f"\n{'='*60}")
        click.echo(f"Project: {project['name']} (ID: {project['id']})")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {project['status']}")
        click.echo(f"Description: {project.get('description', 'N/A')}")
        click.echo(f"Created: {project['created_at']}")
        click.echo(f"Updated: {project['updated_at']}")
        click.echo(f"\nStatistics:")
        click.echo(f"  - Images: {project.get('image_count', 0)}")
        click.echo(f"  - Annotations: {project.get('annotation_count', 0)}")
        click.echo(f"  - Labels: {project.get('label_count', 0)}")

        if project.get('labels'):
            click.echo(f"\nLabels:")
            for label in project['labels']:
                click.echo(f"  - {label['name']} ({label['color']})")

        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command('create')
@click.option('--name', prompt=True, help='Project name')
@click.option('--description', default='', help='Project description')
@click.option('--labels', help='Labels as JSON array: [{"name":"car","color":"#ff0000"}]')
@click.pass_context
def create_project(ctx, name: str, description: str, labels: str):
    """Create a new project."""
    client: APIClient = ctx.obj['client']

    try:
        labels_list = json.loads(labels) if labels else None
        project = client.create_project(name=name, description=description, labels=labels_list)
        click.echo(f"✓ Created project: {project['name']} (ID: {project['id']})")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command('update')
@click.argument('project_id', type=int)
@click.option('--name', help='New project name')
@click.option('--description', help='New description')
@click.option('--status', type=click.Choice(['active', 'archived']), help='Project status')
@click.pass_context
def update_project(ctx, project_id: int, name: str, description: str, status: str):
    """Update project."""
    client: APIClient = ctx.obj['client']

    updates = {}
    if name:
        updates['name'] = name
    if description:
        updates['description'] = description
    if status:
        updates['status'] = status

    if not updates:
        click.echo("No updates provided.")
        return

    try:
        project = client.update_project(project_id, **updates)
        click.echo(f"✓ Updated project: {project['name']} (ID: {project['id']})")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command('delete')
@click.argument('project_id', type=int)
@click.confirmation_option(prompt='Are you sure you want to delete this project?')
@click.pass_context
def delete_project(ctx, project_id: int):
    """Delete a project."""
    client: APIClient = ctx.obj['client']

    try:
        client.delete_project(project_id)
        click.echo(f"✓ Deleted project ID: {project_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command('add-label')
@click.argument('project_id', type=int)
@click.option('--name', prompt=True, help='Label name')
@click.option('--color', default='#1890ff', help='Label color (hex)')
@click.pass_context
def add_label(ctx, project_id: int, name: str, color: str):
    """Add a label to project."""
    client: APIClient = ctx.obj['client']

    try:
        label = client.add_label(project_id, name=name, color=color)
        click.echo(f"✓ Added label: {label['name']} (ID: {label['id']})")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
