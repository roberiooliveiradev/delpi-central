import click
from flask.cli import with_appcontext

from app.application.services.chat_admin_settings_bundle_service import (
    ChatAdminSettingsBundleService,
)
from app.composition.repository_composer import make_admin_runtime_settings_repository
from app.composition.chat_composer import make_chat_intelligence_settings_service
from app.infrastructure.config.chat_admin_settings_bundles import (
    CHAT_LEARNING_PIPELINE_BUNDLE,
    CHAT_RESPONSE_MODE_BUNDLE,
    CHAT_VISION_BUNDLE,
)
from app.extensions.db import db


def _seed_bundle(service: ChatAdminSettingsBundleService) -> None:
    service.ensure_defaults_seeded()


@click.command("seed-chat-platform-settings")
@with_appcontext
def seed_chat_platform_settings_command() -> None:
    """Garante defaults de inteligência, modos, visão e aprendizagem (admin prevalece)."""
    repository = make_admin_runtime_settings_repository()

    make_chat_intelligence_settings_service().ensure_defaults_seeded()

    for spec in (
        CHAT_RESPONSE_MODE_BUNDLE,
        CHAT_VISION_BUNDLE,
        CHAT_LEARNING_PIPELINE_BUNDLE,
    ):
        _seed_bundle(ChatAdminSettingsBundleService(spec, repository))

    db.session.commit()
    click.echo("Configurações de plataforma do chat verificadas (seed só se vazio).")
