import click
from flask.cli import with_appcontext

from app.composition.chat_composer import make_chat_intelligence_settings_service
from app.extensions.db import db


@click.command("sync-chat-intelligence-env")
@with_appcontext
def sync_chat_intelligence_env_command() -> None:
    """Espelha CHAT_* / RAG_* / EXTERNAL_ACTION_* do .env no runtime admin."""
    service = make_chat_intelligence_settings_service()
    service.sync_from_environment()
    db.session.commit()
    click.echo("Inteligência do chat sincronizada a partir do .env.")
