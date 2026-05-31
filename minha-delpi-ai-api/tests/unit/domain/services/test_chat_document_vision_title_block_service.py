from app.domain.services.chat_document_vision_title_block_service import (
    ChatDocumentVisionTitleBlockService,
)


def test_build_title_block_from_stamp_and_codes():
    block = ChatDocumentVisionTitleBlockService.build(
        text="OUTRO TEXTO",
        product_code="90260140",
        revision="03",
        stamp_text="PRODUTO 90260140\nREV. 03",
    )

    assert block is not None
    assert block["fields"]["code"] == "90260140"
    assert block["fields"]["rev"] == "03"
    assert "PRODUTO" in block["rawText"]
    assert len(block["bbox"]) == 4


def test_build_title_block_extracts_code_from_stamp_text():
    block = ChatDocumentVisionTitleBlockService.build(
        text="",
        product_code=None,
        revision=None,
        stamp_text="PRODUTO 90260140\nREV. 03",
    )

    assert block is not None
    assert block["fields"]["code"] == "90260140"
    assert block["fields"]["rev"] == "03"


def test_build_title_block_returns_none_without_signal():
    assert (
        ChatDocumentVisionTitleBlockService.build(
            text="texto genérico sem carimbo",
            product_code=None,
            revision=None,
        )
        is None
    )
