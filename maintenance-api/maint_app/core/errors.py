from __future__ import annotations

import logging

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)

_logger = logging.getLogger(__name__)

_GENERIC_MESSAGE = "Erro interno do servidor."


def format_api_error(exc: Exception) -> str:
    """Loga detalhes internos e retorna mensagem segura para o cliente."""
    _logger.debug("api_error_detail: %s", exc, exc_info=True)

    if isinstance(exc, (ValueError, PluginsRepositoryError)):
        msg = str(exc)
        if msg and len(msg) < 300:
            return msg

    return _GENERIC_MESSAGE
