"""Detecção e respostas diretas sobre identidade do assistente/agente."""

import pytest

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)

_SHOULD_DETECT = (
    ("quem é vc?", "who"),
    ("quem é você?", "who"),
    ("quem e vc", "who"),
    ("se apresente", "who"),
    ("o que vc faz?", "role"),
    ("para que serve", "role"),
    ("o que você não faz", "limits"),
    ("suas limitações", "limits"),
    ("você é ia?", "origin"),
    ("como foi feito", "origin"),
    ("como usar o chat", "usage"),
    ("como te usar", "usage"),
)

_SHOULD_NOT_DETECT = (
    "quem sou eu",
    "meu perfil",
    "sobre mim",
    "estoque do 10080001",
    "o que você pode fazer?",
    "quais suas capacidades",
    "ajuda",
    "fornecedores do 10080001",
)


@pytest.mark.parametrize("message,category", _SHOULD_DETECT)
def test_identity_detection_positive(message: str, category: str):
    assert ChatAssistantIdentityService.classify(message) == category, message


@pytest.mark.parametrize("message", _SHOULD_NOT_DETECT)
def test_identity_detection_negative(message: str):
    assert ChatAssistantIdentityService.classify(message) is None, message


def test_who_answer_uses_agent_name():
    text = ChatAssistantIdentityService.build_direct_answer(
        message="quem é vc?",
        workspace_context={
            "agent": {
                "name": "Agente Minha DELPI",
                "description": "foco em cadastro e consultas de produto.",
            },
            "agentId": "11111111-1111-4111-8111-111111111111",
        },
    )
    assert text
    assert "Agente Minha DELPI" in text
    assert "cadastro e consultas de produto" in text


def test_who_answer_platform_without_agent():
    text = ChatAssistantIdentityService.build_direct_answer(
        message="quem é você?",
        workspace_context={"agent": None, "agentId": None},
    )
    assert text
    assert "Minha DELPI" in text
    assert "Especialista" not in text


def test_user_identity_not_assistant():
    assert ChatAssistantIdentityService.classify("quem sou eu") is None


def test_what_identity_detects_o_que_vc_e():
    assert ChatAssistantIdentityService.classify("o que vc é?") == "what"
