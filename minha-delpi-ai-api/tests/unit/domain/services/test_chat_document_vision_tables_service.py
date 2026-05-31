from app.domain.services.chat_document_vision_tables_service import (
    ChatDocumentVisionTablesService,
)


def test_extract_markdown_table():
    text = """
    LISTA DE MATERIAIS
    | Código | Qtd | Descrição |
    |--------|-----|-----------|
    | 90260141 | 2 | TERMINAL |
    | 90260142 | 1 | CABO |
    """

    tables = ChatDocumentVisionTablesService.extract_tables(text)

    assert len(tables) == 1
    assert tables[0]["columns"][0] == "Código"
    assert tables[0]["rows"][0][0] == "90260141"


def test_extract_tsv_block():
    text = "Header1\tHeader2\nVal1\tVal2\nVal3\tVal4"

    tables = ChatDocumentVisionTablesService.extract_tables(text)

    assert len(tables) == 1
    assert tables[0]["format"] == "tsv"
    assert tables[0]["rowCount"] == 2
