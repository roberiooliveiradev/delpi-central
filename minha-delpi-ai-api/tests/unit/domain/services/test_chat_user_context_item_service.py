from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


def test_auto_items_capture_product_as_neutral_context():
    items = ChatUserContextItemService.auto_items_from_entities(
        {"productCode": "90260114", "productCodeSource": "tool", "branch": "02"},
    )

    by_kind = {item["kind"]: item for item in items}

    assert len(items) == 2
    assert all(item["kind"] == "context" for item in items)
    assert items[0]["label"] == "90260114"
    assert items[0]["extractedEntities"]["productCode"] == "90260114"
    assert items[1]["label"] == "02"


def test_auto_items_skip_inferred_product_code():
    items = ChatUserContextItemService.auto_items_from_entities(
        {"productCode": "000224", "productCodeSource": "inferred"},
    )

    assert all(item["kind"] != "product" for item in items)


def test_auto_items_dedupe_against_existing():
    existing = [
        {"id": "x", "extractedEntities": {"productCode": "90260114"}},
    ]
    items = ChatUserContextItemService.auto_items_from_entities(
        {"productCode": "90260114", "productCodeSource": "explicit"},
        existing,
    )

    assert items == []


def test_classify_product_short_text():
    result = ChatUserContextItemService.classify("10080001")

    assert result["kind"] == "context"
    assert result["label"] == "10080001"
    assert result["extractedEntities"]["productCode"] == "10080001"


def test_classify_branch_short_text_preserves_user_phrase():
    result = ChatUserContextItemService.classify("filial 01")

    assert result["kind"] == "context"
    assert result["label"] == "filial 01"
    assert result["extractedEntities"]["branch"] == "01"


def test_classify_table_markdown():
    content = "| produto | qtd |\n| --- | --- |\n| A | 1 |"
    result = ChatUserContextItemService.classify(content)

    assert result["kind"] == "table"


def test_classify_long_text_as_note():
    result = ChatUserContextItemService.classify(
        "Na reunião de ontem combinamos revisar o cronograma de entregas com o time."
    )

    assert result["kind"] == "note"


def test_ingest_question_from_user_role():
    item = ChatUserContextItemService.ingest(
        content="Qual o estoque do produto 10080001?",
        role="user",
        message_id="msg-1",
    )

    assert item["kind"] == "question"
    assert item["role"] == "user"
    assert item["messageId"] == "msg-1"
    assert "Pergunta" in item["label"]


def test_ingest_answer_from_assistant_role():
    item = ChatUserContextItemService.ingest(
        content="O estoque disponível é 120 unidades.",
        role="assistant",
    )

    assert item["kind"] == "answer"
    assert item["role"] == "assistant"
    assert "Resposta" in item["label"]


def test_ingest_turn_returns_question_and_answer():
    items = ChatUserContextItemService.ingest_turn(
        question="Compare com o anterior",
        answer="A diferença principal é o lead time.",
        question_message_id="u1",
        answer_message_id="a1",
    )

    assert len(items) == 2
    assert items[0]["kind"] == "question"
    assert items[1]["kind"] == "answer"


def test_dedup_key_stable_for_same_message():
    item = ChatUserContextItemService.ingest(
        content="Monte uma consulta SA1",
        role="user",
        message_id="msg-sa1",
    )

    assert ChatUserContextItemService.dedup_key_for_item(item) == "msg:msg-sa1:question"
    chip = ChatUserContextItemService.chip_from_item(item)

    assert chip["value"] == "msg:msg-sa1:question"
    assert chip["kind"] == "question"


def test_find_duplicate_item_ids_for_repeated_question():
    existing = [
        ChatUserContextItemService.ingest(
            content="Pergunta antiga",
            role="user",
            message_id="msg-1",
        )
    ]
    incoming = [
        ChatUserContextItemService.ingest(
            content="Pergunta nova",
            role="user",
            message_id="msg-1",
        )
    ]

    remove_ids = ChatUserContextItemService.find_duplicate_item_ids(existing, incoming)

    assert remove_ids == [existing[0]["id"]]


def test_chip_from_item_branch_uses_entity_value_not_item_id():
    item = ChatUserContextItemService.ingest(content="filial 01")

    assert item["kind"] == "context"
    assert item["extractedEntities"]["branch"] == "01"

    chip = ChatUserContextItemService.chip_from_item(item)

    assert chip["kind"] == "context"
    assert chip["value"] == "01"
    assert chip["label"] == "filial 01"
    assert chip.get("itemId") == item["id"]


def test_build_context_chips_no_duplicate_branch_entity_and_user_item():
    from app.domain.services.chat_conversation_memory_service import (
        ChatConversationMemoryService,
    )

    item = ChatUserContextItemService.ingest(content="filial 02")
    snapshot = {
        "lastEntities": {"productCode": "90260146", "branch": "02"},
        "userContextItems": [item],
    }

    chips = ChatConversationMemoryService.build_context_chips(snapshot)
    branch_value_chips = [chip for chip in chips if chip.get("value") == "02"]

    assert len(branch_value_chips) == 1
    assert branch_value_chips[0]["kind"] == "context"


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
