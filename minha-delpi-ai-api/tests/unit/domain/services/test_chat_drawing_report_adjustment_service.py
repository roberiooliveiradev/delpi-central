from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_drawing_report_adjustment_turn_service import (
    ChatDrawingReportAdjustmentTurnService,
)
from app.domain.entities.chat_message import ChatMessage
from app.domain.services.chat_drawing_report_adjustment_intent_service import (
    ChatDrawingReportAdjustmentIntentService,
)
from app.domain.services.chat_drawing_report_adjustment_service import (
    ChatDrawingReportAdjustmentService,
)


def _analysis_90261877() -> dict:
    return {
        "status": "approved_with_notes",
        "overallLabel": "Aprovado com ressalvas",
        "productCode": "90261877",
        "hasPdfAttachment": True,
        "pdfLegible": True,
        "criticalErrors": 0,
        "errors": 0,
        "warnings": 1,
        "items": [
            {
                "section": "Cotas",
                "item": "Nota dimensional ambígua",
                "status": "pending",
                "templateKey": "dimension_note_ambiguous",
                "pdfEvidence": "Nota de termo",
                "apiEvidence": "—",
                "recommendation": "Conferir manualmente",
            },
            {
                "section": "Produto",
                "item": "Produto encontrado",
                "status": "ok",
                "templateKey": "product_found",
                "pdfEvidence": "—",
                "apiEvidence": "90261877",
                "recommendation": "—",
            },
        ],
        "conclusion": "Revise os itens pendentes.",
    }


def _history_with_analysis(analysis: dict | None = None) -> list[dict]:
    return [
        {
            "role": "assistant",
            "metadata": {
                "drawingAnalysis": analysis or _analysis_90261877(),
                "drawingAnalysisExport": {"markdown": "# Relatório"},
            },
        }
    ]


def _history_with_chat_message_entity(analysis: dict | None = None) -> list[ChatMessage]:
    return [
        ChatMessage(
            id=uuid4(),
            session_id=uuid4(),
            role="assistant",
            content="# Relatório de Análise de Desenho DELPI",
            metadata={
                "drawingAnalysis": analysis or _analysis_90261877(),
                "drawingAnalysisExport": {"markdown": "# Relatório"},
            },
            created_at=datetime.now(timezone.utc),
        )
    ]


def test_intent_matches_chip_confirm_manual_message():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )

    assert ChatDrawingReportAdjustmentIntentService.matches(message)


def test_chip_message_not_classified_as_drawing_analysis_request():
    from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )

    assert not ChatDrawingIntentService.is_drawing_analysis_request(message)


def test_chip_adjustment_turn_updates_report_to_approved():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=_history_with_analysis(),
    )

    assert result is not None
    assert result["drawingAnalysis"]["status"] == "approved"
    assert "Relatório de Análise" in result["directAnswer"]
    assert result["drawingAnalysisExport"]["markdown"]


def test_chip_adjustment_reads_chat_message_entity_history():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=_history_with_chat_message_entity(),
    )

    assert result is not None
    assert result["drawingAnalysis"]["status"] == "approved"
    assert result["drawingAnalysisExport"]["markdown"]


def test_adjustment_without_prior_report_returns_direct_answer_not_none():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=[],
    )

    assert result is not None
    assert result["toolCalls"] == []
    assert "relatório de análise de desenho anterior" in str(result["directAnswer"]).lower()


def test_intent_matches_90261877_adjustment_message():
    message = (
        "foi revisado e o problema não é verdadeiro, gere um novo relatório"
    )

    assert ChatDrawingReportAdjustmentIntentService.matches(message)


def test_intent_matches_conferido_correction_phrase():
    assert ChatDrawingReportAdjustmentIntentService.matches(
        "conferido e esta correto",
    )


def test_adjustment_turn_updates_dimension_note_to_approved():
    message = (
        "foi revisado e o problema não é verdadeiro, gere um novo relatório"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=_history_with_analysis(),
    )

    assert result is not None
    analysis = result["drawingAnalysis"]
    assert analysis["status"] == "approved"
    assert analysis["overallLabel"] == "Aprovado"
    assert analysis["warnings"] == 0

    ambiguous = next(
        item
        for item in analysis["items"]
        if item.get("templateKey") == "dimension_note_ambiguous"
    )
    assert ambiguous["status"] == "ok"
    assert ambiguous.get("manualReview") is True
    assert "Revisado em engenharia" in str(ambiguous.get("pdfEvidence") or "")

    assert result["drawingAnalysisExport"]["markdown"]
    assert "Relatório de Análise" in result["directAnswer"]
    assert len(result["drawingAnalysisOverrides"]) == 1


def test_apply_overrides_recalculates_summary():
    analysis = _analysis_90261877()
    override = ChatDrawingReportAdjustmentService.build_override(
        template_key="dimension_note_ambiguous",
        analysis=analysis,
    )
    updated = ChatDrawingReportAdjustmentService.apply_overrides(
        analysis,
        [override],
    )

    assert updated["status"] == "approved"
    assert updated["warnings"] == 0


def test_rejects_critical_override():
    analysis = {
        "productCode": "90260140",
        "hasPdfAttachment": True,
        "items": [
            {
                "section": "BOM",
                "item": "Componente ausente",
                "status": "critical_error",
                "templateKey": "bom_missing",
            }
        ],
    }
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        "foi revisado, não é verdadeiro, gere novo relatório",
        previous_messages=_history_with_analysis(analysis),
    )

    assert result is not None
    assert "erro crítico" in str(result.get("directAnswer") or "").lower()


def test_ambiguous_when_multiple_adjustable_items():
    analysis = {
        "productCode": "90260140",
        "hasPdfAttachment": True,
        "items": [
            {
                "section": "Cotas",
                "item": "Nota ambígua",
                "status": "pending",
                "templateKey": "dimension_note_ambiguous",
            },
            {
                "section": "BOM",
                "item": "Qtd divergente",
                "status": "error",
                "templateKey": "bom_quantity_mismatch",
            },
        ],
    }
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        "foi revisado em engenharia",
        previous_messages=_history_with_analysis(analysis),
    )

    assert result is not None
    assert "Qual item devo marcar" in str(result.get("directAnswer") or "")
