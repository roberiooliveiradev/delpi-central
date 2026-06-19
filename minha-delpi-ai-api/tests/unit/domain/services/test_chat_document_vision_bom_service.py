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


def test_score_bom_text_penalizes_vista_without_codes():
    assert ChatDocumentVisionBomService.score_bom_text('VISTA "A"') < 0


def test_is_stamp_layout_without_bom_detects_revision_block():
    text = (
        "MEDIDAS EM MILÍMETRO\n"
        "CLIENTE: WEG\n"
        "CHICOTE DE LIGAÇÃO | 90263396"
    )

    assert ChatDocumentVisionBomService.is_stamp_layout_without_bom(text) is True


def test_extract_bom_rows_skips_ptc_temperature_suffix_code():
    text = "A | 01 | 10250032 | TERMISTOR PTC 130°C 10084053"

    rows = ChatDocumentVisionBomService.extract_bom_rows(
        text,
        exclude_product_code="90262019",
        region_scoped=True,
    )

    assert [row["code"] for row in rows] == ["10250032"]


def test_meaningful_bom_component_codes_excludes_finished_product_rows():
    rows = [
        {"code": "90263396", "quantity": None},
        {"code": "10080591", "quantity": "01"},
    ]

    codes = ChatDocumentVisionBomService.meaningful_bom_component_codes(
        rows,
        exclude_product_code="90263396",
    )

    assert codes == ["10080591"]


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

