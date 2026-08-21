from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "12-roadmap-e-evolucao"
    / "commercial"
    / "API-ROUTES.md"
).read_text(encoding="utf-8")

_OPERATION_IDS = (
    "list_interaction_rooms",
    "resolve_interaction_room",
    "get_interaction_room",
    "list_interaction_room_members",
    "add_interaction_room_member",
    "remove_interaction_room_member",
    "mark_interaction_room_read",
    "list_interaction_messages",
    "post_interaction_message",
    "update_interaction_message",
    "delete_interaction_message",
    "set_interaction_message_reaction",
    "clear_interaction_message_reaction",
    "list_interaction_room_shared_items",
    "list_interaction_room_pins",
    "pin_interaction_message",
    "unpin_interaction_message",
    "suggest_interaction_mentions",
    "preview_interaction_entity",
    "create_task_from_interaction_message",
)

_FORBIDDEN_PT_PATHS = (
    "/sala",
    "/mencoes",
    "/interacao",
)


def test_api_routes_section_lists_all_operation_ids() -> None:
    assert "### 3.21" in DOC
    missing = [op for op in _OPERATION_IDS if op not in DOC]
    assert not missing, f"operationId ausente no § 3.21: {missing}"


def test_api_routes_has_no_portuguese_interaction_paths() -> None:
    section = DOC.split("### 3.21")[-1].split("## 4.")[0].lower()
    for path in _FORBIDDEN_PT_PATHS:
        assert path not in section, f"path PT no § 3.21: {path}"


def test_attachments_and_tasks_note_room_message() -> None:
    assert "room_message" in DOC
    assert "source_interaction_message_id" in DOC
    assert "Sala de interação" in DOC or "P2-SALA" in DOC
    assert "post_system_message" in DOC
    assert "task_ref_message" in DOC


def test_message_contract_markdown_limits_and_parent() -> None:
    section = DOC.split("### 3.21")[-1].split("## 4.")[0]
    assert "markdown" in section.lower()
    assert "422" in section
    assert "parent_id" in section
    assert "20 MB" in section or "20MB" in section
    assert "mentions" in section.lower()
    assert "attachment:" in section
    assert "pending:" in section
    assert "belowBody" in section
