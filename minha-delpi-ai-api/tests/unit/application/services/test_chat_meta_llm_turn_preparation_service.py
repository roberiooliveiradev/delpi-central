from app.application.services.chat_meta_llm_turn_preparation_service import (
    ChatMetaLlmTurnPreparationService,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
)


def test_capabilities_question_routes_to_llm_synthesis():
    caps = "Posso ajudar você nestes formatos:\n\n- RAG"
    result = ChatMetaLlmTurnPreparationService.apply_meta_llm_route(
        message="o que você pode fazer?",
        workspace_context={},
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _message: None,
        resolve_capabilities_facts=lambda _message: caps,
        resolve_assistant_identity_facts=lambda _message: None,
    )

    assert result.active is True
    assert result.skip_rag is True
    assert result.skip_meta_direct_answer is True
    assert result.skip_isolated_meta_direct_answers is True
    assert caps in result.tool_context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS]


def test_assistant_identity_question_routes_to_llm_synthesis():
    identity = "Olá! Sou o **Assistente Minha DELPI**."
    result = ChatMetaLlmTurnPreparationService.apply_meta_llm_route(
        message="quem é você?",
        workspace_context={},
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _message: None,
        resolve_capabilities_facts=lambda _message: None,
        resolve_assistant_identity_facts=lambda _message: identity,
    )

    assert result.active is True
    assert identity in result.tool_context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS]
