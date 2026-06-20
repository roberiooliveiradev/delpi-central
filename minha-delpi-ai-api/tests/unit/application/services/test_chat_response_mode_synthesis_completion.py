def test_resolve_authorized_persisted_answer_skips_when_llm_synthesis_effect():
    from app.domain.services.chat_operational_narrative_synthesis_service import (
        ChatOperationalNarrativeSynthesisService,
    )
    from app.domain.services.chat_tool_context_presentation_service import (
        ChatToolContextPresentationService,
    )

    authorized = "### Status fabril\n\nSituação consolidada: **PA PRODUZIDO**."
    llm_answer = "O produto 90269002 está PA PRODUZIDO hoje, com leitura consultiva."
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90269002/factory-status",
                "textPresentation": {
                    "type": "markdown",
                    "markdown": authorized,
                },
                "presentationDecision": {
                    "layoutMode": "stack",
                    "presentationMode": "summary_then_evidence",
                },
            },
        }
    ]

    assert ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect("llm_synthesis")

    persisted = ChatToolContextPresentationService.resolve_authorized_persisted_answer(
        llm_answer,
        tool_calls,
        message="qual o status do produto 90269002 na fabrica hoje?",
        skip_replacement=True,
    )

    assert persisted == llm_answer
    assert persisted != authorized
