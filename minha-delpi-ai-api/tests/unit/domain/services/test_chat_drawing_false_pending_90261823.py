"""Regressão — falsas pendências estilo 90261823 (MP cotas, balão OCR, REF haystack)."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_balloon_validation_service import (
    ChatDrawingBalloonValidationService,
)
from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_customer_reference_cross_check_service import (
    ChatDrawingCustomerReferenceCrossCheckService,
)
from app.domain.services.chat_drawing_dimensions_extraction_service import (
    ChatDrawingDimensionsExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()

_PRODUCT = "90261823"


def _root_90261823() -> dict:
    return {
        "product": {
            "code": _PRODUCT,
            "customer_reference": "10432385",
            "drawing_code": "Z-667G012",
            "unit": "MI",
        },
        "structure": {
            "items": [
                {
                    "code": "10350006",
                    "quantity": 1000.0,
                    "unit": "MI",
                    "description": "ABRAÇADEIRA 3,6X150MM NATURAL - ROHS",
                },
                {
                    "code": "10500017",
                    "quantity": 1000.0,
                    "unit": "MI",
                    "description": (
                        "TUBO ISOLANTE 12,00X0,80 PT 130°C 1,5KV PVC COMP 750MM"
                    ),
                },
                {
                    "code": "50222629",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA0,75BRAN-01005/14/06-0000-1100",
                },
                {
                    "code": "50231401",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA0,75PRET-01005/14/06-0000-1145",
                },
                {
                    "code": "50231405",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA0,75VDAR-01008/06/06-2100-1145",
                },
                {
                    "code": "50231925",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA0,75MRBN-00285/14/06-0000-1145",
                },
            ]
        },
    }


def test_parse_mp_description_length_mm_tubo_and_abracadeira():
    assert 750.0 in ChatDrawingBomQuantitySemanticsService.parse_mp_description_length_mm(
        "TUBO ISOLANTE 12,00X0,80 PT 130°C PVC COMP 750MM"
    )
    assert 150.0 in ChatDrawingBomQuantitySemanticsService.parse_mp_description_length_mm(
        "ABRAÇADEIRA 3,6X150MM NATURAL - ROHS"
    )


def test_structure_segment_reference_includes_mp_description_mm():
    refs = ChatDrawingBomQuantitySemanticsService.collect_structure_segment_reference_mm(
        _root_90261823()
    )

    assert 750.0 in refs
    assert 150.0 in refs


def test_filter_plausible_drops_ocr_garbage_keeps_real_segments():
    filtered = ChatDrawingDimensionsExtractionService.filter_plausible_segment_lengths(
        [750.0, 150.0, 31008.0, 1005.0]
    )

    assert 31008.0 not in filtered
    assert 750.0 in filtered
    assert 1005.0 in filtered


def test_segment_length_pending_ignores_mp_description_and_ocr_garbage():
    pdf_extract = {
        "legible": True,
        "dimensions": {
            "segmentLengthsMm": [750.0, 150.0, 31008.0, 1005.0, 1008.0, 285.0],
        },
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_root_90261823(),
        pdf_extract=pdf_extract,
        product_code=_PRODUCT,
    )
    pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert not pending


def test_balloon_ignores_component_code_phantoms_when_structured_bom():
    pdf_extract = {
        "componentCodes": [
            "10020008",
            "10020048",
            "50231405",
            "50231925",
            "10350006",
            "10500017",
        ],
        "bomRows": [
            {"code": "10350006", "quantity": "1"},
            {"code": "10500017", "quantity": "1"},
            {"code": "50231405", "quantity": "1"},
            {"code": "50231925", "quantity": "1"},
        ],
        "bomVisionRefinement": {"columnRowCount": 4},
        "sourceMetadata": {},
    }

    items = ChatDrawingBalloonValidationService.build_check_items(pdf_extract=pdf_extract)

    assert any(item.get("templateKey") == "balloon_presence_ok" for item in items)
    assert not any(item.get("templateKey") == "balloon_missing_codes" for item in items)


def test_customer_reference_ok_when_in_configured_source_metadata_haystack():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract={
            "sourceMetadata": {
                "stampText": "CARIMBO SEM REF",
                "cadReferenceText": "REF: 10432385",
            }
        },
    )

    assert item is not None
    assert item.get("templateKey") == "customer_reference_ok"
    assert item.get("status") == "ok"
