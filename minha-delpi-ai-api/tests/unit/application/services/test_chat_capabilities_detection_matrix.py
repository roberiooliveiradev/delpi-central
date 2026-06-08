"""Matriz de frases para detecção de pergunta de capacidades (sem LLM)."""

import pytest

from app.application.services.chat_capabilities_service import ChatCapabilitiesService

_SHOULD_DETECT = (
    "o que você pode fazer?",
    "o que vc pode fazer",
    "o que vc é capaz de fazer?",
    "o que voce e capaz de fazer",
    "do que voce e capaz",
    "o que você pode fazer",
    "do que vc e capaz de fazer",
    "quais suas capacidades",
    "suas funcionalidades",
    "ajuda",
    "help",
    "comandos",
    "capacidades",
    "menu",
    "o que da pra consultar",
    "quais apis",
    "quais actions",
    "menu de comandos",
    "como voce pode me ajudar",
    "como você pode ajudar",
    "o que vc faz?",
    "no que voce ajuda",
    "quais suas funcoes",
    "para que serve voce",
    "o que faz aqui",
    "me diga o que pode fazer",
    "me mostre o que da pra fazer",
    "pode consultar o que",
    "quais ferramentas",
    "ajuda com estoque",  # prefixo ajuda
)

_SHOULD_NOT_DETECT = (
    "estoque do 10080001",
    "fornecedores do produto 10080001 em tabela",
    "forncedores do 10080001",
    "quanto tem em estoq do 10080001",
    "estrutura do 10080001",
    "listar lmps da filial 01",
    "preço do produto 10080025",
    "o superadmin é capaz de tudo no sistema",
    "ele é capaz de resolver sozinho",
    "quanto custa o produto",
    "SELECT * FROM SB1010 LIMIT 1",
)


@pytest.mark.parametrize("message", _SHOULD_DETECT)
def test_capabilities_detection_positive(message: str):
    assert ChatCapabilitiesService.is_capabilities_question(message), message


@pytest.mark.parametrize("message", _SHOULD_NOT_DETECT)
def test_capabilities_detection_negative(message: str):
    assert not ChatCapabilitiesService.is_capabilities_question(message), message


def test_capabilities_answer_has_expected_structure_common_chat():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": None, "agentId": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert "chat comum" in text.lower()
    assert "Posso ajudar você nestes formatos:" in text
    assert "Consultas operacionais" in text
    assert "fornecedores do 10080001" in text
    assert "Robério" not in text
    assert "Gerenciamento de Permissões" not in text


def test_capabilities_answer_with_agent_includes_examples():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": {"name": "Especialista em Produtos"}, "agentId": "11111111-1111-4111-8111-111111111111"},
        allowed_action_ids=["act.stock", "act.suppliers"],
        action_catalog=[
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/api/v1/products/{code}/stock",
                "summary": "Estoque do produto",
            },
            {
                "actionId": "act.suppliers",
                "method": "GET",
                "path": "/api/v1/products/{code}/suppliers",
                "summary": "Fornecedores",
            },
        ],
    )
    assert "Especialista em Produtos" in text
    assert "estoque do produto 10080001" in text
    assert any("fornecedor" in line.lower() for line in text.splitlines())
