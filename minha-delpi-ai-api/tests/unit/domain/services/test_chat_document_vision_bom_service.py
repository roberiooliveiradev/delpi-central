from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService


def test_extract_bom_rows_from_lista_materiais():
    text = """
    PRODUTO 90260140 REV.03
    LISTA DE MATERIAIS
    90260141  2  TERMINAL PINO
    90260142  1,5  CABO FLEX
    """

    rows = ChatDocumentVisionBomService.extract_bom_rows(
        text,
        exclude_product_code="90260140",
    )

    assert len(rows) == 2
    assert rows[0]["code"] == "90260141"
    assert rows[0]["quantity"] == "2"
    assert "TERMINAL" in (rows[0].get("description") or "")


def test_merge_into_drawing_parse_includes_bom_rows():
    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        {"productCode": "90260140", "componentCodes": []},
        {
            "engine": "tesseract",
            "stages": ["tesseract", "bom_heuristic"],
            "bomRows": [
                {"code": "90260141", "quantity": "2", "description": "TERMINAL"},
            ],
            "componentCodes": ["90260141"],
        },
    )

    assert merged["bomRows"][0]["code"] == "90260141"
    assert "90260141" in merged["componentCodes"]
    assert merged["documentVision"]["bomRowCount"] == 1
    assert merged["bomHints"][0]["componentCode"] == "90260141"
    assert merged["bomHints"][0]["evidence"] == "bom_heuristic"
