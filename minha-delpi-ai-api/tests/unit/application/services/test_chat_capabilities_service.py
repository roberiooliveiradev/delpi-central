from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def test_is_capabilities_question():
    assert ChatCapabilitiesService.is_capabilities_question("o que você pode fazer?")
    assert ChatCapabilitiesService.is_capabilities_question("quais suas capacidades")
    assert ChatCapabilitiesService.is_capabilities_question("o que da pra consultar")
    assert ChatCapabilitiesService.is_capabilities_question("ajuda")
    assert ChatCapabilitiesService.is_capabilities_question("o que vc é capaz de fazer?")
    assert not ChatCapabilitiesService.is_capabilities_question("o que vc faz?")
    assert not ChatCapabilitiesService.is_capabilities_question("estoque do 10080001")


def test_build_direct_answer_common_chat():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": None, "agentId": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert text
    assert "chat comum" in text.lower() or "agente" in text.lower()
    assert "get_current_user" not in text


def test_build_direct_answer_with_agent_actions():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": {"name": "Especialista"}, "agentId": "11111111-1111-4111-8111-111111111111"},
        allowed_action_ids=["act.stock"],
        action_catalog=[
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "summary": "Estoque do produto",
            },
        ],
    )
    assert "Especialista" in text
    assert "Estoque" in text
    assert "/products/" in text
    assert "estoque do produto 10080001" in text


def test_build_direct_answer_common_includes_examples():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": None, "agentId": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert "fornecedores do 10080001" in text
    assert "pequenos erros de digitação" in text.lower() or "erros de digitacao" in text.lower()


def test_build_direct_answer_includes_business_suggestions():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": None, "agentId": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert "visão 360" in text.lower() or "visao 360" in text.lower()
    assert "cruzam várias fontes" in text.lower() or "cruzam varias fontes" in text.lower()


def test_resolve_path_rule_suppliers():
    category, examples = ChatCapabilitiesService._resolve_path_rule(
        "/api/v1/products/{code}/suppliers"
    )
    assert category == "Fornecedores de produto"
    assert any("fornecedor" in ex for ex in examples)


def test_capability_inquiry_group_search_with_typo():
    message = "vc coonsegue buscar um produto pelo seu grupo?"
    assert ChatCapabilitiesService.is_capability_inquiry(message)
    assert not ChatCapabilitiesService._looks_like_operational_command(
        ChatMessageNormalizationService.normalize_for_matching(message)
    )

    answer = ChatCapabilitiesService.build_feature_answer(
        message=message,
        workspace_context={
            "agent": {"name": "Especialista em Produtos"},
            "agentId": "11111111-1111-4111-8111-111111111111",
        },
        allowed_action_ids=["act.search"],
        action_catalog=[
            {
                "actionId": "act.search",
                "method": "GET",
                "path": "/products/search",
                "parametersSchema": [
                    {"name": "description"},
                    {"name": "group_code"},
                    {"name": "page_size"},
                ],
            }
        ],
    )

    assert answer
    assert "group_code" in answer
    assert "Atenção" not in answer


def test_operational_search_is_not_capability_inquiry():
    assert not ChatCapabilitiesService.is_capability_inquiry("liste 3 exemplos de TERM")
    assert ChatCapabilitiesService.is_capability_inquiry("o que você pode fazer?")


def test_qual_estoque_with_product_code_runs_operational_not_capabilities():
    message = "qual o estoque do produto 90260015?"

    assert not ChatCapabilitiesService.is_capability_inquiry(message)
    assert ChatCapabilitiesService.resolve_capability_answer(
        message=message,
        workspace_context={"agent": {"name": "Agente"}, "agentId": "x"},
        allowed_action_ids=["act.stock"],
        action_catalog=[
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "summary": "Estoque",
            }
        ],
    ) is None


def test_capability_inquiry_without_agent_explains_common_chat():
    answer = ChatCapabilitiesService.build_feature_answer(
        message="você consegue buscar produto por grupo?",
        workspace_context={"agent": None, "agentId": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert answer
    assert "chat comum" in answer.lower() or "agente" in answer.lower()
