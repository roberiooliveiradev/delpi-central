from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)


def test_parse_from_text_extracts_code_and_revision():
    text = """
    DESENHO TÉCNICO DELPI
    CÓDIGO 90260140
    REV. 02
    DESCRIÇÃO CHICOTE TESTE
    """

    parsed = ChatDrawingPdfExtractionService.parse_from_text(text)

    assert parsed["productCode"] == "90260140"
    assert parsed["revision"] == "02"
    assert parsed["legible"] is True


def test_parse_from_attachment_context_block():
    context = (
        "Conteúdo dos arquivos anexados:\n\n"
        "### desenho.pdf\n"
        "CODIGO 90264130 REV.00 CLIENTE WEG\n"
    )

    parsed = ChatDrawingPdfExtractionService.parse_from_attachment_context(context)

    assert parsed is not None
    assert parsed["productCode"] == "90264130"
    assert parsed["revision"] == "00"


def test_parse_extracts_components_and_dimensions():
    text = """
    CODIGO 90260140 REV.01
    COMPONENTE 50212194
    COMPRIMENTO TOTAL 1400 mm
    DECAPE ESQUERDO 10
    DECAPE DIREITO 12
    """

    parsed = ChatDrawingPdfExtractionService.parse_from_text(text)

    assert "50212194" in parsed["componentCodes"]
    assert parsed["dimensions"]["totalLengthMm"] == 1400.0
    assert parsed["dimensions"]["leftDecapeMm"] == 10.0


def test_parse_illegible_short_text():
    parsed = ChatDrawingPdfExtractionService.parse_from_text("abc")

    assert parsed["legible"] is False
    assert parsed["productCode"] is None


def test_parse_from_text_propagates_page_count_from_metadata():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "CODIGO DELPI 90263622 REV.01 CHICOTE DE LIGACAO",
        metadata={"pageCount": 10, "pagesProcessed": 10, "filename": "90263622.pdf"},
    )

    assert parsed["pageCount"] == 10
    assert parsed["pagesProcessed"] == 10


def test_parse_from_text_propagates_page_layout_analysis_from_regions():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "CODIGO DELPI 90264227 REV.02",
        metadata={
            "regions": {
                "_layoutAnalysis": {
                    "algorithm": "xy_cut_semantic_v1",
                    "confidence": 0.72,
                    "semanticRegions": {"bom": [0.0, 0.0, 0.5, 0.35]},
                }
            }
        },
    )

    layout = parsed.get("pageLayoutAnalysis") or {}

    assert layout.get("algorithm") == "xy_cut_semantic_v1"
    assert layout.get("confidence") == 0.72
