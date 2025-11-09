"""Configuration management commands."""

import click
import yaml
import sys
from pathlib import Path
from typing import Optional


@click.group('config')
def config():
    """Manage configuration files."""
    pass


@config.command('init')
@click.option('--env', type=click.Choice(['development', 'production', 'test']),
              default='development', help='Environment type')
@click.option('--output', '-o', default='config.yaml', help='Output file path')
@click.option('--force', is_flag=True, help='Overwrite existing file')
def init_config(env: str, output: str, force: bool):
    """Initialize a new configuration file."""
    output_path = Path(output)

    if output_path.exists() and not force:
        click.echo(f"Error: {output} already exists. Use --force to overwrite.", err=True)
        raise click.Abort()

    # Determine source template
    config_dir = Path(__file__).parent.parent.parent.parent / 'configs'
    template_file = config_dir / f'config.{env}.yaml'

    if not template_file.exists():
        template_file = config_dir / 'config.example.yaml'

    if not template_file.exists():
        click.echo("Error: No configuration template found.", err=True)
        raise click.Abort()

    # Copy template to output
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        click.echo(f"✓ Created configuration file: {output}")
        click.echo(f"Environment: {env}")
        click.echo("\nNext steps:")
        click.echo("1. Edit the configuration file with your settings")
        click.echo("2. Use 'qwen3vl-annotate config validate' to check it")
        click.echo("3. Set environment variable: export QWEN3VL_CONFIG=config.yaml")
    except Exception as e:
        click.echo(f"Error creating config file: {e}", err=True)
        raise click.Abort()


@config.command('validate')
@click.argument('config_file', type=click.Path(exists=True))
def validate_config(config_file: str):
    """Validate a configuration file."""
    try:
        # Import here to avoid circular imports
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from backend.core.config_loader import ConfigLoader

        config = ConfigLoader.load_from_file(config_file)

        click.echo(f"✓ Configuration file is valid: {config_file}")
        click.echo(f"\nEnvironment: {config.environment.value}")
        click.echo(f"Debug: {config.debug}")
        click.echo(f"\nDatabase: {config.database.host}:{config.database.port}/{config.database.database}")
        click.echo(f"Redis: {config.redis.host}:{config.redis.port}/{config.redis.db}")
        click.echo(f"API: {config.api.host}:{config.api.port}")
        click.echo(f"Storage: {config.storage.root}")

        # Warnings
        warnings = []
        if config.environment.value == 'production' and config.debug:
            warnings.append("⚠ Debug mode is enabled in production environment")
        if config.database.password == "":
            warnings.append("⚠ Database password is empty")
        if config.models.hunyuan_api_key is None:
            warnings.append("⚠ Hunyuan API key is not set")

        if warnings:
            click.echo("\nWarnings:")
            for warning in warnings:
                click.echo(warning)

    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        raise click.Abort()


@config.command('show')
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--section', help='Show specific section only')
def show_config(config_file: str, section: Optional[str]):
    """Display configuration file contents."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if section:
            if section in data:
                data = {section: data[section]}
            else:
                click.echo(f"Error: Section '{section}' not found", err=True)
                raise click.Abort()

        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
    except Exception as e:
        click.echo(f"Error reading config file: {e}", err=True)
        raise click.Abort()


@config.command('get')
@click.argument('config_file', type=click.Path(exists=True))
@click.argument('key')
def get_config_value(config_file: str, key: str):
    """Get a specific configuration value."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Support nested keys with dot notation (e.g., database.host)
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                click.echo(f"Error: Key '{key}' not found", err=True)
                raise click.Abort()

        click.echo(value)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@config.command('set')
@click.argument('config_file', type=click.Path(exists=True))
@click.argument('key')
@click.argument('value')
def set_config_value(config_file: str, key: str, value: str):
    """Set a configuration value."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # Support nested keys with dot notation
        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Try to convert value to appropriate type
        try:
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.lower() == 'null':
                value = None
            elif value.isdigit():
                value = int(value)
            elif '.' in value and all(p.isdigit() for p in value.split('.', 1)):
                value = float(value)
        except:
            pass  # Keep as string

        current[keys[-1]] = value

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        click.echo(f"✓ Updated {key} = {value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@config.command('merge')
@click.argument('base_config', type=click.Path(exists=True))
@click.argument('override_config', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file (defaults to base config)')
def merge_configs(base_config: str, override_config: str, output: Optional[str]):
    """Merge two configuration files."""
    try:
        with open(base_config, 'r', encoding='utf-8') as f:
            base_data = yaml.safe_load(f) or {}

        with open(override_config, 'r', encoding='utf-8') as f:
            override_data = yaml.safe_load(f) or {}

        # Deep merge
        def deep_merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(base_data, override_data)

        output_file = output or base_config
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(base_data, f, default_flow_style=False, sort_keys=False)

        click.echo(f"✓ Merged configurations into: {output_file}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@config.command('list-templates')
def list_templates():
    """List available configuration templates."""
    config_dir = Path(__file__).parent.parent.parent.parent / 'configs'

    if not config_dir.exists():
        click.echo("No configuration templates found.")
        return

    templates = list(config_dir.glob('config.*.yaml'))

    if not templates:
        click.echo("No configuration templates found.")
        return

    click.echo("Available configuration templates:")
    for template in sorted(templates):
        name = template.stem.replace('config.', '')
        click.echo(f"  - {name}: {template}")
