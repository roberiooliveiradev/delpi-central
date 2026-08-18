from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V004 = (ROOT / "migrations" / "V004__attachments.sql").read_text(encoding="utf-8")
V019 = (ROOT / "migrations" / "V019__interaction_rooms.sql").read_text(encoding="utf-8")


def test_v004_attachments_owner_types_unchanged() -> None:
    assert "CHECK (owner_type IN ('task', 'customer', 'activity'))" in V004
    assert "room_message" not in V004


def test_v019_creates_interaction_room_tables() -> None:
    for table in (
        "commercial.interaction_rooms",
        "commercial.interaction_room_members",
        "commercial.interaction_messages",
        "commercial.interaction_mentions",
        "commercial.interaction_reactions",
        "commercial.interaction_pins",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in V019


def test_v019_room_kind_and_message_kind_checks() -> None:
    assert "kind IN ('entity', 'process', 'wall')" in V019
    assert "message_kind IN ('text', 'system', 'task_ref', 'pin')" in V019
    assert "role IN ('member', 'watcher')" in V019


def test_v019_partial_uniques_for_entity_and_wall() -> None:
    assert "WHERE kind = 'entity' AND deleted_at IS NULL" in V019
    assert "WHERE kind = 'wall' AND deleted_at IS NULL" in V019


def test_v019_extends_attachments_owner_type_without_rewriting_v004() -> None:
    assert "ALTER TABLE commercial.attachments" in V019
    assert "room_message" in V019
    assert "DROP TABLE" not in V019
    assert "V004__attachments.sql" not in V019
