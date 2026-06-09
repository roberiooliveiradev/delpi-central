import json

from app.application.services.chat_tool_context_auxiliary_service import (
    ChatToolContextAuxiliaryService,
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


def test_build_drawing_analysis_enrichment_uses_response_preview():
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
    auxiliary = ChatToolContextAuxiliaryService(
        presenter=ExternalActionResultPresenter(),
        formatter=formatter,
    )

    result = auxiliary._build_drawing_analysis_enrichment(
        safe_tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {"code": "90260140"},
                "metadata": safe_metadata,
            }
        ],
        product_code="90260140",
        has_pdf_attachment=True,
        direct_answer="### Informações completas do produto",
        pdf_extract={"productCode": "90260140", "revision": "01", "legible": True},
    )

    assert result is not None
    drawing = result["drawingAnalysis"]
    assert drawing["productCode"] == "90260140"
    assert len(drawing["items"]) > 1
    assert "Relatório de Análise" in str(result["directAnswer"])
    assert "Informações completas" in str(result["directAnswer"])
