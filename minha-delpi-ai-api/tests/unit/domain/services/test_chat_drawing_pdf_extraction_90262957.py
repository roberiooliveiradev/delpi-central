"""Regressão — desenho 90262957 (chicote ligação WEG, cotas CAD 1127±2)."""

from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)

_CAD_REFERENCE = """
CHICOTE DE LIGAÇÃO | 90262957
WEG INDUSTRIA S.A - LINHARES
A
B
C
10±1
1127±2
E
B
C
10±1
1127±2
D
B
C
10±1
1127±2
F
B
C
10±1
1127±2
MEDIDAS EM MILÍMETROS
"""

_FUSED_OCR_NOISE = """
ABC 10±11127±2
EBC 10±11127±2
DBC 10±11127±2
FBC 10±11127±2
50232502 | CAO,75MRBN-01127/06/10-0945-0000
"""


def test_parse_90262957_uses_cad_reference_for_dimensions():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        _FUSED_OCR_NOISE,
        metadata={
            "filename": "90262957.pdf",
            "cadReferenceText": _CAD_REFERENCE,
        },
    )

    dims = parsed.get("dimensions") or {}

    assert parsed.get("productCode") == "90262957"
    assert dims.get("totalLengthMm") == 1127.0
    assert dims.get("leftDecapeMm") is None
    assert dims.get("rightDecapeMm") == 10.0
    assert dims.get("segmentLengthsMm") == [1127.0, 1127.0, 1127.0, 1127.0]
    assert 11127.0 not in (dims.get("segmentLengthsMm") or [])


def test_parse_90262957_title_block_from_cad_reference():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "",
        metadata={
            "filename": "90262957.pdf",
            "cadReferenceText": _CAD_REFERENCE,
        },
    )

    title = parsed.get("titleBlock") or {}
    fields = title.get("fields") or {}

    assert parsed.get("productCode") == "90262957"
    assert fields.get("code") == "90262957"
    assert "CHICOTE" in str(parsed.get("description") or "").upper()
