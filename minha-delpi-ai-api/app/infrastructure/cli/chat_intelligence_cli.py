import click
from flask.cli import with_appcontext

from app.composition.chat_composer import make_chat_intelligence_settings_service
from app.extensions.db import db


@click.command("sync-chat-intelligence-env")
@with_appcontext
def sync_chat_intelligence_env_command() -> None:
    """Garante defaults iniciais de inteligência (não sobrescreve configuração admin)."""
    service = make_chat_intelligence_settings_service()
    service.ensure_defaults_seeded()
    db.session.commit()
    click.echo("Inteligência do chat: defaults aplicados apenas se ainda não configurado.")


@click.command("seed-chat-intelligence-defaults")
@with_appcontext
def seed_chat_intelligence_defaults_command() -> None:
    """Alias explícito para seed de defaults de inteligência."""
    service = make_chat_intelligence_settings_service()
    service.ensure_defaults_seeded()
    db.session.commit()
    click.echo("Defaults de inteligência do chat verificados.")
