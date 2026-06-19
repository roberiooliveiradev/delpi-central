from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)


def test_demote_bom_codes_in_candidates_caps_confidence():
    candidates = [
        {"code": "10400006", "source": "stamp_context", "confidence": 0.55},
        {"code": "90261040", "source": "stamp_labeled", "confidence": 0.92},
    ]

    demoted = ChatDocumentVisionBomService.demote_bom_codes_in_candidates(
        candidates,
        ["10400006"],
    )

    assert demoted[0]["confidence"] == 0.5
    assert demoted[0]["source"].endswith("_bom_demoted")
    assert demoted[1]["confidence"] == 0.92


def test_score_bom_text_penalizes_vista_without_codes():
    assert ChatDocumentVisionBomService.score_bom_text('VISTA "A"') < 0


def test_resolve_from_sources_prefers_stamp_when_bom_region_is_noise():
    noisy_bom = 'VISTA "A"\nLIGACAO'
    stamp_text = """
1    10080591       TERM. PINO 18-22AWG EMO2 FEMEA ESTANHADO
) 1      10090481          CONECTOR MODULAR MACHO 4 POLOS
"""

    rows, codes, source = ChatDocumentVisionBomService.resolve_from_sources(
        [
            ("bom_region", noisy_bom),
            ("stamp_region", stamp_text),
            ("full_text", stamp_text),
        ],
        exclude_product_code="90262019",
    )

    assert source in {"stamp_region", "full_text"}
    assert codes == ["10080591", "10090481"]
    assert [row["code"] for row in rows] == ["10080591", "10090481"]


def test_parse_from_text_recovers_components_when_bom_region_is_garbage():
    full_text = """
CHICOTE DE LIGACAO 90262019
1    10080591       TERM. PINO 18-22AWG EMO2 FEMEA ESTANHADO
) 1      10090481          CONECTOR MODULAR MACHO 4 POLOS
REV.: 10
"""
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        full_text,
        metadata={
            "bomText": 'VISTA "A"',
            "stampText": full_text,
        },
    )

    assert parsed["productCode"] is None or parsed["productCode"] == "90262019"
    assert parsed["componentCodes"] == ["10080591", "10090481"]
    assert parsed.get("bomSource") in {"stamp_region", "full_text"}
