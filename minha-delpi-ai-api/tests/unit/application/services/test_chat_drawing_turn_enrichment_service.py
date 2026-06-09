import json

from app.application.services.chat_drawing_turn_enrichment_service import (
    ChatDrawingTurnEnrichmentService,
)
from app.application.services.chat_tool_context_external_action_formatter import (
    ChatToolContextExternalActionFormatter,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def _analyser_tool_call() -> dict:
    payload = _analyser_payload_with_guide_and_inspection()
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    metadata = {
        "ok": True,
        "statusCode": 200,
        "path": "/products/90260140/analyser",
    }
    safe_metadata = formatter._build_safe_tool_metadata(
        "execute_external_action",
        metadata,
        {"data": payload},
    )

    return {
        "name": "execute_external_action",
        "arguments": {"code": "90260140"},
        "metadata": safe_metadata,
    }


def test_enrich_tool_context_from_drawing_intent_without_mode_flag():
    tool_context = {
        "context": "",
        "toolCalls": [_analyser_tool_call()],
        "directAnswer": "### Informações completas do produto",
    }

    enriched = ChatDrawingTurnEnrichmentService.enrich_tool_context(
        tool_context,
        message="Analise o desenho 90260140 e gere o relatório de conformidade DELPI",
        attachment_ids=["att-1"],
    )

    assert enriched.get("drawingAnalysisMode") is True
    assert enriched.get("drawingAnalysis", {}).get("productCode") == "90260140"
    assert "Relatório de Análise" in str(enriched.get("directAnswer"))
    assert enriched["drawingAnalysisExport"]["markdown"]


def test_resolve_report_direct_answer_prefers_export_markdown():
    report = "# Relatório de Análise de Desenho DELPI\n\nOK"
    direct = ChatDrawingTurnEnrichmentService.resolve_report_direct_answer(
        {
            "drawingAnalysisExport": {"markdown": report},
            "directAnswer": "outro texto",
        }
    )

    assert direct == report


def test_build_client_metadata_slice():
    slice_payload = ChatDrawingTurnEnrichmentService.build_client_metadata_slice(
        {
            "drawingAnalysisMode": True,
            "drawingAnalysis": {"productCode": "90260140"},
            "drawingAnalysisExport": {"markdown": "# Relatório"},
        }
    )

    assert slice_payload["drawingAnalysisMode"] is True
    assert slice_payload["drawingAnalysis"]["productCode"] == "90260140"
    assert slice_payload["drawingAnalysisExport"]["markdown"] == "# Relatório"
