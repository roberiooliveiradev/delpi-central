"""Smoke de integração — desenho 90262008 (âncora PDF real, não substitui testes por regra)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.fixtures.drawing_validation_rule_regression_cases import (
    payload_stamp_bom_nested_mp,
    pdf_extract_stamp_bom_nested_mp,
)

configure_domain_infrastructure_ports()

_PRODUCT_CODE = "90262008"


def test_90262008_integration_smoke_no_bom_or_guide_criticals():
    """Smoke único por SKU — regras detalhadas em test_chat_drawing_validation_rule_regression."""
    root = payload_stamp_bom_nested_mp()
    pdf_extract = pdf_extract_stamp_bom_nested_mp()

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code=_PRODUCT_CODE,
    )

    bom_extra = [item for item in items if item.get("templateKey") == "bom_extra"]
    bom_missing_connector = [
        item
        for item in items
        if item.get("templateKey") == "bom_missing"
        and "10090062" in str(item.get("apiEvidence") or "")
    ]
    guide_critical = [
        item
        for item in items
        if item.get("templateKey") == "guide_component_mismatch"
    ]
    segment_pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert not bom_extra
    assert not bom_missing_connector
    assert not guide_critical
    assert not segment_pending


def test_90262008_integration_smoke_revision_ok_end_to_end():
    payload = {
        "product": {
            "code": _PRODUCT_CODE,
            "current_revision": "004",
            "last_revision_date": "20260619",
        },
        "structure": payload_stamp_bom_nested_mp()["structure"],
        "guide": {"items": [], "total": 0},
        "inspection": {"items": []},
    }
    pdf_extract = {
        **pdf_extract_stamp_bom_nested_mp(),
        "revision": "08",
        "internalRevision": "04",
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=_PRODUCT_CODE,
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )

    revision_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("item") == "Revisão"
    ]
    false_bom_critical = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("templateKey") in {"bom_extra", "bom_missing", "guide_component_mismatch"}
        and item.get("status") == "critical_error"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "ok"
    assert not false_bom_critical
