from __future__ import annotations

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)


def format_api_error(exc: Exception) -> str:
    """Extrai mensagem útil de exceções de banco/repositório."""
    if isinstance(exc, PluginsRepositoryError) and exc.__cause__ is not None:
        return str(exc.__cause__)

    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        return str(cause)

    return str(exc) or exc.__class__.__name__
