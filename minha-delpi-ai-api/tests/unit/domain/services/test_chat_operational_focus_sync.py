from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


def test_sync_operational_focus_prefers_context_items_over_stale_entities():
    snapshot = ChatUserContextItemService.sync_operational_focus(
        {
            "operationalFocus": {"productCode": "10080047", "branch": "01"},
            "userContextItems": [
                {
                    "id": "1",
                    "kind": "context",
                    "label": "10080055",
                    "content": "10080055",
                    "extractedEntities": {"productCode": "10080055"},
                },
                {
                    "id": "2",
                    "kind": "context",
                    "label": "filial 02",
                    "content": "filial 02",
                    "extractedEntities": {"branch": "02"},
                },
            ],
        }
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080055"
    assert snapshot["operationalFocus"]["branch"] == "02"
    assert "lastEntities" not in snapshot
    assert "activeEntities" not in snapshot


def test_sync_operational_focus_keeps_history_when_no_context_items():
    snapshot = ChatUserContextItemService.sync_operational_focus(
        {
            "operationalFocus": {"productCode": "10080047", "productCodeSource": "tool"},
            "userContextItems": [],
        }
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080047"
    assert snapshot["operationalFocus"]["productCodeSource"] == "tool"


def test_remove_context_items_for_operational_kind():
    items = [
        {
            "id": "a",
            "extractedEntities": {"productCode": "10080047"},
        },
        {
            "id": "b",
            "extractedEntities": {"branch": "02"},
        },
    ]
    kept, removed = ChatUserContextItemService.remove_context_items_for_operational_kind(
        items,
        kind="product",
    )

    assert removed == ["a"]
    assert len(kept) == 1
    assert kept[0]["id"] == "b"
