from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_revision_cross_check_service import (
    ChatDrawingRevisionCrossCheckService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()


def test_stamp_trusted_when_title_block_present():
    assert ChatDrawingRevisionCrossCheckService.stamp_trusted(
        {"titleBlock": {"revision": "02"}}
    )


def test_stamp_untrusted_without_title_block():
    assert not ChatDrawingRevisionCrossCheckService.stamp_trusted(
        {"revision": "00", "internalRevision": "00"}
    )


def test_revision_mismatch_pending_without_title_block():
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
        },
    )
    revision_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("item") == "Revisão"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "pending"
    assert revision_items[0]["templateKey"] == "revision_manual_pending"


def test_revision_mismatch_critical_with_title_block():
    item = ChatDrawingValidationOrchestrationService._build_revision_cross_check_item(
        pdf_revision="00",
        pdf_internal_revision="00",
        api_current_revision="002",
        api_revision_date="",
        pdf_extract={
            "titleBlock": {"revision": "00", "productCode": "90264226"},
        },
    )

    assert item is not None
    assert item["status"] == "critical_error"
    assert item["templateKey"] == "revision_critical"
