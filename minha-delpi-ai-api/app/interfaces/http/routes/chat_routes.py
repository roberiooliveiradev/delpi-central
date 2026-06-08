"""Compat: reexporta o blueprint modular de `routes.chat`."""

from app.interfaces.http.routes.chat import chat_bp

__all__ = ["chat_bp"]
