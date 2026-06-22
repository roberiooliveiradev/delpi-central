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
        response_mode_effect="llm_synthesis",
        response_mode="normal",
    )

    assert persisted == llm_answer
    assert persisted != authorized


def test_resolve_authorized_persisted_answer_backfills_from_data_commentary_when_llm_empty():
    from app.domain.services.chat_tool_context_presentation_service import (
        ChatToolContextPresentationService,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "dataCommentary": {
                    "summary": "O produto **10080045** — TERM. OLHAL M6.",
                    "attention": ["Plano de inspeção não cadastrado."],
                },
            },
        }
    ]

    persisted = ChatToolContextPresentationService.resolve_authorized_persisted_answer(
        "",
        tool_calls,
        message="me fale do produto 10080045",
        skip_replacement=True,
        response_mode_effect="llm_synthesis",
        response_mode="fast",
    )

    assert "10080045" in persisted
    assert "inspeção" in persisted.lower()
