from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_drawing_report_adjustment_turn_service import (
    ChatDrawingReportAdjustmentTurnService,
)
from app.domain.entities.chat_message import ChatMessage
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.services.chat_drawing_validation_package_service import (
    ChatDrawingValidationPackageService,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def _analysis_90261877() -> dict:
    return {
        "status": "approved_with_notes",
        "overallLabel": "Aprovado com ressalvas",
        "productCode": "90261877",
        "revisionPdf": "01",
        "revisionApi": "20260708",
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


def _full_prior_markdown() -> str:
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261877",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        api_status_code=200,
        pdf_extract={"productCode": "90261877", "revision": "01", "legible": True},
    )
    return ChatDrawingValidationOrchestrationService.format_report_markdown(package)


def _history_with_prior_export(analysis: dict | None = None) -> list[ChatMessage]:
    prior_markdown = _full_prior_markdown()

    return [
        ChatMessage(
            id=uuid4(),
            session_id=uuid4(),
            role="assistant",
            content=prior_markdown,
            metadata={
                "drawingAnalysis": analysis or _analysis_90261877(),
                "drawingAnalysisExport": {"markdown": prior_markdown},
            },
            created_at=datetime.now(timezone.utc),
        )
    ]


def _history_with_validation_package(analysis: dict | None = None) -> list[ChatMessage]:
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261877",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        api_status_code=200,
        pdf_extract={"productCode": "90261877", "revision": "01", "legible": True},
    )
    package["drawingAnalysis"] = analysis or _analysis_90261877()

    return [
        ChatMessage(
            id=uuid4(),
            session_id=uuid4(),
            role="assistant",
            content="# Relatório",
            metadata={
                "drawingAnalysis": analysis or _analysis_90261877(),
                "drawingValidationPackage": ChatDrawingValidationPackageService.strip_for_metadata(
                    package
                ),
            },
            created_at=datetime.now(timezone.utc),
        )
    ]


def test_adjustment_splices_operational_sections_from_prior_export_markdown():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=_history_with_prior_export(),
    )

    markdown = result["drawingAnalysisExport"]["markdown"]

    assert result["drawingAnalysis"]["status"] == "approved"
    assert "### Estrutura (SG1010)" in markdown
    assert "### Roteiro (SG2010)" in markdown
    assert "### Inspeções (QP6 / QP7 / QP8)" in markdown
    assert "## 5. Checklist completo" in markdown
    assert "Aprovado" in markdown


def test_adjustment_uses_persisted_validation_package_for_full_report():
    message = (
        "confirmar revisão manual do item pendente no relatório do desenho 90261877"
    )
    result = ChatDrawingReportAdjustmentTurnService.resolve_tool_context_result(
        message,
        previous_messages=_history_with_validation_package(),
    )

    markdown = result["drawingAnalysisExport"]["markdown"]

    assert "### Estrutura (SG1010)" in markdown
    assert "### Roteiro (SG2010)" in markdown
    assert result["drawingValidationPackage"]["analyserRoot"]
