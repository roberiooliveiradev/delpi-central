import click
from flask.cli import with_appcontext


@click.group("data-retention")
def data_retention_cli():
    """Comandos de retenção de dados (LGPD)."""
    pass


@data_retention_cli.command("run")
@with_appcontext
def run_retention():
    """Executa limpeza periódica de dados que excederam prazo de retenção."""
    from app.infrastructure.jobs.data_retention_job import run_data_retention
    results = run_data_retention()
    for key, value in results.items():
        click.echo(f"  {key}: {value}")
    click.echo("Retenção concluída.")
