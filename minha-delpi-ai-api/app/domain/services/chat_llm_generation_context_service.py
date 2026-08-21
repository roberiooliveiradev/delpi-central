"""Contexto por requisição para parâmetros LLM (modo rápida/normal/pensador)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token

from app.domain.entities.llm_generation_config import LlmGenerationConfig
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_response_mode_service import ChatResponseModeService

_generation_config: ContextVar[LlmGenerationConfig | None] = ContextVar(
    "llm_generation_config",
    default=None,
)
_llm_provider: ContextVar[str | None] = ContextVar("llm_provider", default=None)
_reasoning_fallback: ContextVar[bool] = ContextVar(
    "llm_reasoning_fallback",
    default=False,
)


def mark_reasoning_fallback(used: bool = True) -> None:
    """Marca que o texto visível veio do campo ``reasoning`` (não de ``content``)."""
    _reasoning_fallback.set(bool(used))


def consume_reasoning_fallback() -> bool:
    """Lê e zera o flag — um turno consome no máximo uma vez no finalize."""
    used = bool(_reasoning_fallback.get())
    _reasoning_fallback.set(False)
    return used


def peek_reasoning_fallback() -> bool:
    return bool(_reasoning_fallback.get())


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


def get_active_llm_provider() -> str:
    active = _llm_provider.get()

    if active:
        return active

    return ChatDomainConfigService.llm_provider()


def set_active_llm_provider(provider: str) -> Token:
    return _llm_provider.set(provider)


def reset_active_llm_provider(token: Token) -> None:
    _llm_provider.reset(token)


@contextmanager
def llm_provider_scope(provider: str):
    token = set_active_llm_provider(provider)

    try:
        yield provider
    finally:
        reset_active_llm_provider(token)
