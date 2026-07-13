from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_revision_cross_check_service import (
    ChatDrawingRevisionCrossCheckService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()

_STAMP_TEXT = (
    "ES EXECUTADO VERIFICADO | LIBERADO | DATA\n"
    "| 20/08/24 00 |\n"
    "90264226 REV.00\n"
)


def test_stamp_trusted_when_stamp_markers_present():
    assert ChatDrawingRevisionCrossCheckService.stamp_trusted(
        {
            "productCode": "90264226",
            "titleBlock": {"rawText": _STAMP_TEXT, "fields": {"code": "90264226"}},
        }
    )


def test_stamp_untrusted_when_title_block_is_bom_table_noise():
    assert not ChatDrawingRevisionCrossCheckService.stamp_trusted(
        {
            "productCode": "90263396",
            "titleBlock": {
                "rawText": "A3 | 1 | 10380013 | CABO | A4 | 1 | 10080063 | TERM",
                "fields": {"code": "90263396", "rev": "00"},
            },
        }
    )


def test_stamp_untrusted_without_title_block():
    assert not ChatDrawingRevisionCrossCheckService.stamp_trusted(
        {"revision": "00", "internalRevision": "00"}
    )


def test_client_revision_never_critical_against_totvs():
    payload = {
        "product": {
            "code": "90264226",
            "current_revision": "002",
        },
        "structure": {"items": []},
        "guide": {"items": []},
        "inspection": {"items": []},
    }
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90264226",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90264226",
            "revision": "00",
            "internalRevision": "00",
            "legible": True,
            "titleBlock": {"rawText": _STAMP_TEXT, "fields": {"code": "90264226"}},
        },
    )
    revision_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if str(item.get("templateKey") or "").startswith("revision_")
        and item.get("templateKey") != "revision_api"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "ok"
    assert revision_items[0]["templateKey"] == "revision_client_not_comparable"
    assert not any(
        item.get("templateKey") == "revision_critical"
        for item in package["drawingAnalysis"]["items"]
    )


def test_ocr_stamp_number_ignored_for_totvs_cross_check():
    """Números OCR no carimbo não são B1_REVATU — revisão Delpi só no TOTVS."""
    item = ChatDrawingValidationOrchestrationService._build_revision_cross_check_item(
        pdf_revision="00",
        pdf_internal_revision="00",
        api_current_revision="002",
        api_revision_date="",
        pdf_extract={
            "productCode": "90264226",
            "revision": "00",
            "internalRevision": "00",
            "legible": True,
            "titleBlock": {"rawText": _STAMP_TEXT, "fields": {"code": "90264226"}},
        },
    )

    assert item is not None
    assert item["status"] == "ok"
    assert item["templateKey"] == "revision_client_not_comparable"
