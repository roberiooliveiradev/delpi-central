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


def test_extract_bom_rows_region_scoped_without_section_header():
    text = """
    POS CODIGO QTD
    01 10400006 2 TERMINAL
    02 90260141 1 CABO
    """

    rows = ChatDocumentVisionBomService.extract_bom_rows(
        text,
        exclude_product_code="90261040",
        region_scoped=True,
    )

    assert [row["code"] for row in rows] == ["10400006", "90260141"]


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


def test_merge_into_drawing_parse_includes_bom_rows():
    from app.application.services.chat_document_vision_service import ChatDocumentVisionService

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

