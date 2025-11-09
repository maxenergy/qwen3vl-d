"""Image management commands."""

import click
from tabulate import tabulate
from ..api_client import APIClient


@click.group('images')
def images():
    """Manage images."""
    pass


@images.command('list')
@click.argument('project_id', type=int)
@click.option('--page', default=1, help='Page number')
@click.option('--review-status', type=click.Choice(['pending', 'approved', 'rejected']),
              help='Filter by review status')
@click.pass_context
def list_images(ctx, project_id: int, page: int, review_status: str):
    """List images."""
    client: APIClient = ctx.obj['client']

    try:
        filters = {}
        if review_status:
            filters['review_status'] = review_status

        result = client.list_images(project_id, page=page, **filters)
        images = result.get('items', [])

        if not images:
            click.echo("No images found.")
            return

        headers = ['ID', 'Filename', 'Review Status', 'Annotations', 'Created']
        rows = []
        for img in images:
            rows.append([
                img['id'],
                img['filename'][:40],
                img.get('review_status', 'pending'),
                img.get('annotation_count', 0),
                img['created_at'][:10]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@images.command('review')
@click.argument('project_id', type=int)
@click.argument('image_id', type=int)
@click.option('--approve/--reject', required=True, help='Approve or reject image')
@click.option('--notes', default='', help='Review notes')
@click.pass_context
def review_image(ctx, project_id: int, image_id: int, approve: bool, notes: str):
    """Review an image."""
    client: APIClient = ctx.obj['client']

    try:
        result = client.review_image(project_id, image_id, approved=approve, notes=notes)
        status = 'approved' if approve else 'rejected'
        click.echo(f"✓ Image {image_id} marked as {status}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
