from app.domain.services.chat_document_vision_title_block_service import (
    ChatDocumentVisionTitleBlockService,
)


def test_build_title_block_from_stamp_and_codes():
    block = ChatDocumentVisionTitleBlockService.build(
        text="OUTRO TEXTO",
        product_code="90260140",
        revision="03",
        stamp_text="CÓDIGO DELPI 90260140\nREV. 03",
    )

    assert block is not None
    assert block["fields"]["code"] == "90260140"
    assert block["fields"]["rev"] == "03"
    assert "CÓDIGO DELPI" in block["rawText"]
    assert len(block["bbox"]) == 4
    assert block["bbox"][1] >= 0.5


def test_build_title_block_extracts_code_from_chicote_title():
    block = ChatDocumentVisionTitleBlockService.build(
        text="CHICOTE DE LIGAÇÃO90264236 COD:DES:REV:00",
        product_code=None,
        revision=None,
        stamp_text="",
    )

    assert block is not None
    assert block["fields"]["code"] == "90264236"


def test_build_title_block_returns_none_without_signal():
    assert (
        ChatDocumentVisionTitleBlockService.build(
            text="texto genérico sem carimbo",
            product_code=None,
            revision=None,
        )
        is None
    )
