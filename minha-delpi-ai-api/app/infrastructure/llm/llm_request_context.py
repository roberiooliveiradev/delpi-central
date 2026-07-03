"""Compat — reexporta contexto LLM do domain (clean architecture)."""

from __future__ import annotations

from app.domain.services.chat_llm_generation_context_service import (
    get_active_config,
    get_active_llm_provider,
    llm_generation_scope,
    llm_provider_scope,
    reset_active_config,
    set_active_config,
)

__all__ = [
    "get_active_config",
    "get_active_llm_provider",
    "llm_generation_scope",
    "llm_provider_scope",
    "reset_active_config",
    "set_active_config",
]
