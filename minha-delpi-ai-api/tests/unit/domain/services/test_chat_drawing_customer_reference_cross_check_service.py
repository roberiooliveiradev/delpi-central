from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_customer_reference_cross_check_service import (
    ChatDrawingCustomerReferenceCrossCheckService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_stamp_extraction_service import (
    ChatDrawingStampExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.services.chat_drawing_validation_rule_registry_service import (
    ChatDrawingValidationRuleRegistryService,
)

configure_domain_infrastructure_ports()

_STAMP_REF = (
    "CHICOTE DE LIGAÇÃO\n"
    "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
    "REF: 10432385\n"
    "90261823 REV: 00\n"
)


def test_stamp_extracts_ref_label_as_customer_code():
    extract = ChatDrawingStampExtractionService.extract(stamp_text=_STAMP_REF)

    assert extract.get("customerCode") == "10432385"


def test_customer_code_labeled_pattern_matches_ref():
    match = ChatDrawingPatternsService.customer_code_labeled().search(_STAMP_REF)

    assert match is not None
    assert match.group(1).strip() == "10432385"


def test_normalize_collapses_spaces_and_case():
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.normalize("3E 4270 G02")
        == "3E4270G02"
    )


def test_customer_reference_ok_when_pdf_matches_api():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="10432385",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_ok"
    assert item["status"] == "ok"


def test_customer_reference_mismatch_is_critical():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="99999999",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_mismatch"
    assert item["status"] == "critical_error"


def test_customer_reference_pending_when_pdf_missing():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="",
        api_reference="10432385",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_pdf"
    assert item["status"] == "pending"


def test_customer_reference_pending_when_api_missing():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_api"
    assert item["status"] == "pending"


def test_rule_registry_enables_customer_reference_cross_check():
    assert ChatDrawingValidationRuleRegistryService.is_enabled(
        "customer_reference_cross_check",
        "90261823",
        group_code="9026",
    )


def test_orchestration_includes_customer_reference_item():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261823",
        payload={
            "product": {
                "code": "90261823",
                "customer_reference": "10432385",
                "current_revision": "004",
            },
            "structure": {"items": []},
            "guide": {"items": []},
            "inspection": {"items": []},
        },
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90261823",
            "revision": "00",
            "customerReference": "10432385",
            "legible": True,
        },
    )
    items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if str(item.get("templateKey") or "").startswith("customer_reference_")
    ]

    assert items
    assert items[0]["templateKey"] == "customer_reference_ok"
    assert package["drawingAnalysis"]["customerReferencePdf"] == "10432385"
    assert package["drawingAnalysis"]["customerReferenceApi"] == "10432385"
