"""Contexto por requisição para parâmetros LLM (modo rápida/normal/pensador)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token

from app.domain.entities.llm_generation_config import LlmGenerationConfig
from app.domain.services.chat_response_mode_service import ChatResponseModeService

_generation_config: ContextVar[LlmGenerationConfig | None] = ContextVar(
    "llm_generation_config",
    default=None,
)


def get_active_config() -> LlmGenerationConfig:
    active = _generation_config.get()

    if active is not None:
        return active

    return ChatResponseModeService.resolve(None)


def set_active_config(config: LlmGenerationConfig) -> Token:
    return _generation_config.set(config)


def reset_active_config(token: Token) -> None:
    _generation_config.reset(token)


@contextmanager
def llm_generation_scope(config: LlmGenerationConfig):
    token = set_active_config(config)

    try:
        yield config
    finally:
        reset_active_config(token)
