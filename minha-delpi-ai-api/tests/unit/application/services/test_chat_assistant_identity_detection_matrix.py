"""Matriz de frases para identidade do assistente (sem LLM)."""

import pytest

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)

_WHO = (
    "quem é vc?",
    "quem e voce",
    "quem é você",
    "se apresente",
    "qual seu nome",
    "como vc se chama",
)

_ROLE = (
    "para que serve",
)

_LIMITS = (
    "o que vc nao faz",
    "suas limitacoes",
    "quais limitações",
)

_ORIGIN = (
    "vc e ia",
    "voce e um bot",
    "como voce funciona",
)

_USAGE = (
    "como usar o chat",
    "como te usar",
    "como falar com voce",
)


@pytest.mark.parametrize("message", _WHO)
def test_matrix_who(message: str):
    assert ChatAssistantIdentityService.classify(message) == "who"


@pytest.mark.parametrize("message", _ROLE)
def test_matrix_role(message: str):
    assert ChatAssistantIdentityService.classify(message) == "role"


@pytest.mark.parametrize("message", _LIMITS)
def test_matrix_limits(message: str):
    assert ChatAssistantIdentityService.classify(message) == "limits"


@pytest.mark.parametrize("message", _ORIGIN)
def test_matrix_origin(message: str):
    assert ChatAssistantIdentityService.classify(message) == "origin"


@pytest.mark.parametrize("message", _USAGE)
def test_matrix_usage(message: str):
    assert ChatAssistantIdentityService.classify(message) == "usage"
