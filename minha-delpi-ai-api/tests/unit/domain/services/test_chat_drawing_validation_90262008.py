"""Regressão — desenho 90262008 (BOM carimbo, roteiro × PI legado, decape global)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_guide_component_consistency_service import (
    ChatDrawingGuideComponentConsistencyService,
)
from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()


def _payload_90262008() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "10090062",
                    "quantity": 1.0,
                    "unit": "PC",
                    "components": [],
                },
                {
                    "code": "10120073",
                    "quantity": 650.0,
                    "unit": "PC",
                    "components": [],
                },
                {
                    "code": "50225424",
                    "description": "CA0,75VDAR-00785/04/06-3800-1000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020007", "quantity": 785.0, "unit": "MT"},
                        {"code": "10080110", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020043", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225426",
                    "description": "CA0,75VERM-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020006", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225427",
                    "description": "CA0,75AZUL-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020042", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225428",
                    "description": "CA0,75PRET-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020046", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
                {
                    "code": "50225429",
                    "description": "CA0,75MARR-00792/04/14-3800-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020048", "quantity": 792.0, "unit": "MT"},
                        {"code": "10080138", "quantity": 1000.0, "unit": "PC"},
                    ],
                },
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "90262008",
                    "component_code": "50221605",
                    "component_description": "CA18VDAR-00792/04/06-4700-1000",
                    "bom_level": 0,
                },
                {
                    "product_code": "90262008",
                    "component_code": "50221606",
                    "component_description": "CA18BRAN-00792/04/14-3800-0000",
                    "bom_level": 0,
                },
            ]
        },
    }


def _pdf_extract_90262008() -> dict:
    return {
        "productCode": "90262008",
        "legible": True,
        "componentCodes": [
            "10020006",
            "10020007",
            "10020042",
            "10020043",
            "10020046",
            "10020048",
            "10080110",
            "10080138",
            "10120073",
        ],
        "intermediateCodes": [],
        "bomRows": [
            {"code": "10120073", "quantity": "12"},
            {"code": "10020007", "quantity": None},
            {"code": "10080110", "quantity": None},
            {"code": "10080138", "quantity": None},
            {"code": "10020043", "quantity": None},
            {"code": "10020006", "quantity": None},
            {"code": "10020042", "quantity": None},
            {"code": "10020046", "quantity": None},
            {"code": "10020048", "quantity": None},
            {"code": "10432635", "quantity": "855", "description": "REV: 08"},
        ],
        "validationScopes": {
            "bom": {
                "sourceKey": "stamp_bom_table",
                "available": True,
                "charCount": 1925,
            },
            "dimensions": {
                "sourceKey": "dimensions_region",
                "available": True,
                "charCount": 1805,
            },
        },
        "sourceMetadata": {
            "stampText": (
                "90262008 REV.08\n"
                "10090062 CONECTOR RETO 6 VIAS NU MACHO UL 94V-2\n"
                "10120073 TUBO ISOLANTE 12,00X0,80\n"
            ),
        },
        "dimensions": {
            "leftDecapeMm": 14.0,
            "rightDecapeMm": None,
            "segmentLengthsMm": [650.0, 792.0, 785.0],
            "cotaDecapeValuesMm": [14.0],
            "decapeIndication": {"left": True, "right": False},
        },
    }


def test_90262008_nested_mp_codes_in_stamp_bom_not_extra():
    result = ChatDrawingBomComparisonService.compare(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    assert not result.extra_in_pdf


def test_90262008_root_mp_found_in_stamp_haystack_not_missing():
    result = ChatDrawingBomComparisonService.compare(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    assert "10090062" not in result.missing_in_pdf


def test_90262008_guide_component_matches_structure_pi_by_fingerprint():
    mismatches = ChatDrawingGuideComponentConsistencyService.compare(
        root=_payload_90262008(),
        product_code="90262008",
    )

    assert not mismatches


def test_90262008_no_false_decape_mismatch_when_global_decape_is_misassigned():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    decape_errors = [
        item
        for item in items
        if item.get("templateKey") == "decape_mismatch"
        and item.get("status") == "error"
    ]

    assert not decape_errors


def test_90262008_structure_validation_without_bom_criticals():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
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

    assert not bom_extra
    assert not bom_missing_connector
    assert not guide_critical


def test_90262008_internal_revision_from_stamp_table_date_row():
    stamp = (
        "ES EXECUTADO VERIFICADO | LIBERADO | DATA\n"
        "| 20/08/24 04 |\n"
        "90262008 REV.08\n"
    )

    assert ChatDrawingPdfExtractionService._extract_internal_revision(stamp) == "04"


def test_90262008_revision_cross_check_ok_when_internal_matches_api():
    payload = {
        "product": {
            "code": "90262008",
            "current_revision": "004",
            "last_revision_date": "20260619",
        },
        "structure": _payload_90262008()["structure"],
        "guide": {"items": [], "total": 0},
        "inspection": {"items": []},
    }
    pdf_extract = {
        **_pdf_extract_90262008(),
        "revision": "08",
        "internalRevision": "04",
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90262008",
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

    assert revision_items
    assert revision_items[0]["status"] == "ok"


def test_90262008_tube_quantity_from_dimension_not_trusted():
    evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    evidence = evidences.get("10120073")

    assert evidence is not None
    assert evidence.trusted is False
    assert evidence.reason == "quantity_from_description"


def test_90262008_tube_quantity_pending_not_critical_mismatch():
    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    codes = {item.code for item in pending}

    assert "10120073" not in codes


def test_90262008_no_false_segment_length_pending_for_structure_piece_qty():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90262008(),
        pdf_extract=_pdf_extract_90262008(),
        product_code="90262008",
    )

    segment_pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert not segment_pending
