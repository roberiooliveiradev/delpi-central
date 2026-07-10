"""Regressão — desenho 90263655 (OCR 5020↔5022, qtd 0, decape D=11 mm)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_intermediate_code_service import (
    ChatDrawingIntermediateCodeService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()


def _payload_90263655() -> dict:
    return {
        "product": {
            "code": "90263655",
            "type": "PA",
            "unit": "MI",
            "description": "CHICOTE DE LIGACAO",
            "conversion_factor": 0.0,
            "pa_reference": {
                "catalog_unit": "MI",
                "catalog_pieces_per_unit": 1000.0,
            },
        },
        "structure": {
            "root": {
                "code": "90263655",
                "description": "CHICOTE DE LIGACAO",
                "type": "PA",
                "unit": "MI",
                "quantity": 1,
            },
            "items": [
                {
                    "code": "10080096",
                    "description": "TERM. LINGUETA 6,30X0,80 1,00-2,50MM2 NU S/ISOLACAO FITADO LONGO TRAVA ROHS",
                    "type": "MP",
                    "unit": "PC",
                    "quantity": 2000.0,
                    "components": [],
                },
                {
                    "code": "10091137",
                    "description": "CONECTOR RETO 4 VIAS NU UL 94V-0",
                    "type": "MP",
                    "unit": "PC",
                    "quantity": 1000.0,
                    "components": [],
                },
                {
                    "code": "50224899",
                    "description": "CB18PRET-00336/06/06-9600-0100",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50224900",
                    "description": "CB18VERM-00318/06/11-9600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50224901",
                    "description": "CB18AZUL-00313/06/11-9600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50224902",
                    "description": "CB18AMAR-00318/06/11-9600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50224903",
                    "description": "CB18LARA-00318/06/11-9600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50224904",
                    "description": "CB18BRAN-00318/06/11-9600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50233492",
                    "description": "CB20PRET-00462/10/06-0000-6387",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
            ],
        },
        "guide": {"items": [{"product_code": "90263655", "bom_level": 0}]},
        "inspection": {"items": [{"product_code": "90263655", "bom_level": 0}]},
    }


def _pdf_extract_90263655() -> dict:
    return {
        "productCode": "90263655",
        "legible": True,
        "componentCodes": [
            "10080096",
            "10091137",
            "50224899",
            "50224900",
            "50224901",
            "50224902",
            "50224903",
            "50224904",
            "50233492",
            "50204901",
        ],
        "intermediateCodes": [
            "50224899",
            "50224900",
            "50224901",
            "50224902",
            "50224903",
            "50224904",
            "50233492",
            "50204901",
        ],
        "bomRows": [
            {
                "code": "10080096",
                "quantity": 0,
                "quantitySource": "column",
                "description": "TERM. LINGUETA 6,30X0,80 1,00-2,50MM2 NU S/ISOLACAO FITADO LONGO TRAVA ROHS",
            },
            {
                "code": "10091137",
                "quantity": 4,
                "quantitySource": "column",
                "description": "CONECTOR RETO 4 VIAS NU UL 94V-0",
            },
            {
                "code": "50233492",
                "quantity": 0,
                "quantitySource": "column",
                "description": "CB20PRET-00462/10/06-0000-6387",
            },
        ],
        "dimensions": {
            "leftDecapeMm": None,
            "rightDecapeMm": 11.0,
            "decapeIndication": {"left": False, "right": True},
            "segmentLengthsMm": [318.0, 336.0, 462.0, 313.0],
            "totalLengthMm": 11.0,
        },
        "extractionConfidence": {
            "score": 0.96,
            "meetsThreshold": True,
        },
    }


def test_90263655_ocr_typo_zero_two_swap():
    assert ChatDrawingIntermediateCodeService.is_ocr_typo_duplicate(
        "50204901",
        "50224901",
    )


def test_90263655_no_false_intermediate_extra_for_50204901():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263655(),
        pdf_extract=_pdf_extract_90263655(),
        product_code="90263655",
    )

    extra = [
        item
        for item in items
        if item.get("templateKey") in {"intermediate_extra", "intermediate_extra_item"}
        and item.get("status") == "critical_error"
    ]

    assert not extra


def test_90263655_no_false_decape_mismatch_when_global_d_conflicts_with_50xx():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263655(),
        pdf_extract=_pdf_extract_90263655(),
        product_code="90263655",
    )

    decape_errors = [
        item
        for item in items
        if item.get("templateKey") == "decape_mismatch"
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not decape_errors


def test_90263655_zero_and_description_quantities_not_critical():
    qty_items = ChatDrawingBomQuantityValidationService.build_check_items(
        root=_payload_90263655(),
        pdf_extract=_pdf_extract_90263655(),
        product_code="90263655",
    )

    critical_qty = [
        item
        for item in qty_items
        if item.get("templateKey") == "bom_quantity_mismatch"
        and item.get("status") == "critical_error"
    ]

    assert not critical_qty


def test_90263655_validation_package_without_false_criticals():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90263655",
        payload=_payload_90263655(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract_90263655(),
    )
    analysis = package.get("drawingAnalysis") or {}

    false_critical_keys = {
        "bom_quantity_mismatch",
        "intermediate_extra",
        "intermediate_extra_item",
        "decape_mismatch",
    }
    false_criticals = [
        item
        for item in analysis.get("items") or []
        if item.get("templateKey") in false_critical_keys
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not false_criticals
