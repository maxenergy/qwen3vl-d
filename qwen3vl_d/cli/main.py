"""Main CLI entry point."""

import click
import os
from typing import Optional
from .api_client import APIClient
from .commands import projects, generation, annotation, datasets, training, images, config


@click.group()
@click.option('--api-url', envvar='API_BASE_URL', default='http://localhost:8000',
              help='Backend API URL')
@click.option('--timeout', default=30, help='Request timeout in seconds')
@click.pass_context
def cli(ctx, api_url: str, timeout: int):
    """
    AI Auto-Annotation Tool CLI

    Manage projects, generate images, annotate data, create datasets, and train models.
    """
    ctx.ensure_object(dict)
    ctx.obj['client'] = APIClient(base_url=api_url, timeout=timeout)


# Register command groups
cli.add_command(projects.projects)
cli.add_command(generation.generation)
cli.add_command(images.images)
cli.add_command(annotation.annotation)
cli.add_command(datasets.datasets)
cli.add_command(training.training)
cli.add_command(config.config)


if __name__ == '__main__':
    cli()
