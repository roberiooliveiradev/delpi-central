"""Testes — paridade checklist items × markdown × export."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)
from app.domain.services.chat_drawing_analysis_export_consistency_service import (
    ChatDrawingAnalysisExportConsistencyService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.fixtures.drawing_validation_rule_regression_cases import (
    payload_stamp_bom_nested_mp,
    pdf_extract_stamp_bom_nested_mp,
)

configure_domain_infrastructure_ports()


def _package_90262008() -> dict:
    payload = {
        "product": {
            "code": "90262008",
            "current_revision": "004",
            "last_revision_date": "20260619",
        },
        "structure": payload_stamp_bom_nested_mp()["structure"],
        "guide": payload_stamp_bom_nested_mp()["guide"],
        "inspection": {"items": [{"code": "QP6"}]},
    }
    pdf_extract = {
        **pdf_extract_stamp_bom_nested_mp(),
        "revision": "08",
        "internalRevision": "04",
    }

    return ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90262008",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )


def test_export_consistency_ok_for_synthetic_package():
    package = _package_90262008()
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)
    export = ChatDrawingReportExportService.build_export_payload(
        package=package,
        report_markdown=report,
    )

    consistency = export.get("checklistConsistency") or {}

    assert consistency.get("ok") is True
    assert not consistency.get("issues")
    assert consistency.get("displayItemCount") == consistency.get("markdownChecklistRows")
    assert consistency.get("exportChecklistRows") == consistency.get("displayItemCount")


def test_validate_detects_markdown_checklist_drift():
    package = _package_90262008()

    result = ChatDrawingAnalysisExportConsistencyService.validate(
        package=package,
        report_markdown="# Relatório sem seção de checklist",
    )

    assert result["ok"] is False
    assert result["issues"]
