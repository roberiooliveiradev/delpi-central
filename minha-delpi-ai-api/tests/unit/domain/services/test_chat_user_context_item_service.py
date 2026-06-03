from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


def test_classify_product_short_text():
    result = ChatUserContextItemService.classify("10080001")

    assert result["kind"] == "product"
    assert result["extractedEntities"]["productCode"] == "10080001"


def test_classify_table_markdown():
    content = "| produto | qtd |\n| --- | --- |\n| A | 1 |"
    result = ChatUserContextItemService.classify(content)

    assert result["kind"] == "table"


def test_classify_long_text_as_note():
    result = ChatUserContextItemService.classify(
        "Na reunião de ontem combinamos revisar o cronograma de entregas com o time."
    )

    assert result["kind"] == "note"


def test_format_prompt_block_includes_user_items():
    block = ChatUserContextItemService.format_prompt_block(
        {
            "userContextItems": [
                {
                    "id": "x",
                    "kind": "note",
                    "label": "Reunião",
                    "content": "Revisar playbook",
                }
            ]
        }
    )

    assert block is not None
    assert "Reunião" in block
    assert "playbook" in block
