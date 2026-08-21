"""Regressão: capacidades em fast/normal sem LLM; thinker com fatos clipados."""

from app.application.services.chat_meta_llm_turn_preparation_service import (
    ChatMetaLlmTurnPreparationService,
)
from app.domain.services.chat_capabilities_content_service import (
    ChatCapabilitiesContentService,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
)


def test_capabilities_catalog_normal_skips_llm_synthesis():
    long_caps = "\n".join(
        [f"- capacidade operacional {i} com texto descritivo" for i in range(100)]
    )
    result = ChatMetaLlmTurnPreparationService.apply_meta_llm_route(
        message="o que você pode fazer?",
        workspace_context={},
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _m: None,
        resolve_capabilities_facts=lambda _m: long_caps,
        resolve_assistant_identity_facts=lambda _m: None,
        response_mode="normal",
    )

    assert result.active is False
    assert result.skip_meta_direct_answer is False
    assert "capabilities" in result.pipeline_stages


def test_capabilities_catalog_thinker_clips_facts_under_budget():
    long_caps = "\n".join(
        [f"- capacidade operacional {i} com texto descritivo longo" for i in range(200)]
    )
    max_chars = ChatCapabilitiesContentService.facts_max_chars_for_mode("thinker")
    assert max_chars is not None and max_chars < len(long_caps)

    result = ChatMetaLlmTurnPreparationService.apply_meta_llm_route(
        message="o que você pode fazer?",
        workspace_context={},
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _m: None,
        resolve_capabilities_facts=lambda _m: long_caps,
        resolve_assistant_identity_facts=lambda _m: None,
        response_mode="thinker",
    )

    assert result.active is True
    facts = result.tool_context[
        ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS
    ]
    assert len(facts) <= max_chars
    assert "capacidade operacional 0" in facts
