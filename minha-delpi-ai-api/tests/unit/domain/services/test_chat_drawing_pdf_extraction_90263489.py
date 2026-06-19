"""Regressão — desenho 90263489 (BOM multinível WEG; revisão vs tabela)."""

from tests.support.drawing_pdf_fixtures import (
    assert_component_codes,
    require_drawing_pdf_with_tesseract,
)

from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

_BOM_REGION_OCR = """
Código | Descrição | Item QTD. | Componente Descrição
90263489 | CHICOTE DE LIGACAO ALT.DESENHO
F | 1 | 10080627 | PROTETOR TERMICO 130°C
G | 1 | 10090482 | LUVA TERMO ENCOLHIVEL
A | 1 | 10091062 | CONECTOR FEMEA 2VIAS MATE-N-LOK NATURAL UL
B | 1 | 10210754 | SELO TRASEIRO 2 VIAS
50225215 | CA22VERM-00489/05/04-1400-0600
C | 1 | 10020033 | CABO PVC 105°C 22AWG VM 600V NBR 9117 V02B
D | 1 | 10080106 | TERM. MAG MATE 1,5 18-22AWG ESTANHADO UL
E | 1 | 10080114 | TERM. PINO 2,06 20-14AWG FEMEA ESTANHADO S - ROHS
50225216 | CA22VERM-00545/05/03-1400-0000
C | 1 | 10020033 | CABO PVC 105°C 22AWG VM 600V NBR 9117 V02B
E | 1 | 10080114 | TERM. PINO 2,06 20-14AWG FEMEA ESTANHADO S - ROHS
50225217 | CA22VERM-00060/04/03-0600-0000
C | 1 | 10020033 | CABO PVC 105°C 22AWG VM 600V NBR 9117 V02B
D | 1 | 10080106 | TERM. MAG MATE 1,5 18-22AWG ESTANHADO UL
"""

_REVISION_NATIVE = """
RESUMO DAS MODIFICACOES
03 22/03/24 ALT.TERM.10081042 P/ 10080114
02 29/06/23 ALT.CABO 10020033 P/ 10020031
01 22/06/23 ALT.10080114 P/10081042 E 10090155 P/10091062
"""


def _payload_90263489() -> dict:
    return {
        "structure": {
            "items": [
                {"code": "10080627", "quantity": 1.0, "components": []},
                {"code": "10090482", "quantity": 1.0, "components": []},
                {"code": "10091062", "quantity": 1.0, "components": []},
                {"code": "10210754", "quantity": 1.0, "components": []},
                {
                    "code": "50225215",
                    "description": "CA22VERM-00489/05/04-1400-0600",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020033", "quantity": 489.0},
                        {"code": "10080106", "quantity": 1.0},
                        {"code": "10080114", "quantity": 1.0},
                    ],
                },
                {
                    "code": "50225216",
                    "description": "CA22VERM-00545/05/03-1400-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020033", "quantity": 545.0},
                        {"code": "10080114", "quantity": 1.0},
                    ],
                },
                {
                    "code": "50225217",
                    "description": "CA22VERM-00060/04/03-0600-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020033", "quantity": 60.0},
                        {"code": "10080106", "quantity": 1.0},
                    ],
                },
            ]
        }
    }


def test_revision_lines_are_not_parsed_as_bom_rows():
    rows = ChatDocumentVisionBomService.extract_bom_rows(
        _REVISION_NATIVE,
        region_scoped=True,
    )

    assert rows == []


def test_parse_with_bom_region_ignores_revision_ghost_codes():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        _REVISION_NATIVE,
        metadata={
            "bomText": _BOM_REGION_OCR,
            "stampText": "90263489\nREV.: 04",
            "filename": "90263489.pdf",
        },
    )

    assert parsed["productCode"] == "90263489"
    assert "10081042" not in parsed["componentCodes"]
    assert "10080627" in parsed["componentCodes"]
    assert "10090482" in parsed["componentCodes"]
    assert "10091062" in parsed["componentCodes"]
    assert "10210754" in parsed["componentCodes"]
    assert parsed["intermediateCodes"] == ["50225215", "50225216", "50225217"]
    assert parsed.get("bomSource") == "bom_region"


def test_90263489_structure_validation_without_false_bom_divergence():
    pdf_extract = ChatDrawingPdfExtractionService.parse_from_text(
        _REVISION_NATIVE,
        metadata={
            "bomText": _BOM_REGION_OCR,
            "stampText": "90263489",
            "filename": "90263489.pdf",
        },
    )

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263489(),
        pdf_extract=pdf_extract,
        product_code="90263489",
    )

    assert not any("ausente no PDF" in str(item.get("item")) for item in items)
    assert not any("extra no PDF" in str(item.get("item")) for item in items)
    assert not any("Intermediário" in str(item.get("item")) and "ausente" in str(item.get("item")) for item in items)


def test_live_extraction_90263489_when_tesseract_available():
    pdf = require_drawing_pdf_with_tesseract("90263489.pdf")

    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf),
        filename="90263489.pdf",
    )

    assert parsed["productCode"] == "90263489"
    assert parsed.get("bomSource") == "bom_region"
    assert_component_codes(
        parsed,
        required={"10080627", "10090482", "10091062", "10210754"},
        forbidden={"10081042"},
    )
    assert parsed["intermediateCodes"] == ["50225215", "50225216", "50225217"]

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263489(),
        pdf_extract=parsed,
        product_code="90263489",
    )

    bom_divergences = [
        item
        for item in items
        if any(
            marker in str(item.get("item", ""))
            for marker in ("ausente no PDF", "extra no PDF")
        )
    ]
    assert bom_divergences == [], bom_divergences
