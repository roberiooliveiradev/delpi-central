"""Rotas HTTP do chat — blueprint único com módulos por domínio."""

from app.interfaces.http.routes.chat.shared import chat_bp

from app.interfaces.http.routes.chat import (  # noqa: F401
    agent_provider_routes,
    agent_routes,
    agent_skill_routes,
    attachment_routes,
    internal_openapi_sync_routes,
    message_routes,
    meta_routes,
    project_routes,
    session_routes,
)

__all__ = ["chat_bp"]
