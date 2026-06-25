"""Regressão — sem «sem dados tabulares» quando há narrativa sem linhas de tabela."""

from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.chat_presentation_generic_decision_service import (
    ChatPresentationGenericDecisionService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


def test_factory_status_zero_rows_with_text_presentation_omits_no_tabular_reason():
    metadata = {
        "path": "/products/90260205/factory-status",
        "apiDelpiResponseMeta": {"entity": "product_factory_status"},
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nSituação fabril: **PA PRODUZIDO**.",
        },
        "availableFormats": ["text", "tree", "table"],
    }

    ChatPresentationDecisionService.enrich_metadata(
        metadata,
        user_message="qual o status fabril hoje do produto 90260205?",
    )

    decision = metadata["presentationDecision"]
    reason = str(decision.get("reason") or "").lower()

    assert decision["selected"] == "text"
    assert "sem dados tabulares" not in reason


def test_generic_zero_rows_without_narrative_keeps_no_tabular_reason():
    reason = ChatPresentationVocabularyService.decision_reason
    text_presentation = {"type": "markdown", "markdown": ""}

    assert ChatPresentationGenericDecisionService._zero_row_reason(
        text_presentation=text_presentation,
        metadata=None,
        reason=reason,
    ) == reason("noTabularData")

    assert ChatPresentationGenericDecisionService._zero_row_reason(
        text_presentation={"type": "markdown", "markdown": "### Status\n\nOK."},
        metadata=None,
        reason=reason,
    ) == ""
