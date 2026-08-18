"""E5.S4 — contrato WS da sala documentado alinhado ao código."""

from __future__ import annotations

from pathlib import Path

from commercial_app.application.services.commercial_realtime_notify import (
    interaction_room_key,
)
from commercial_app.application.services.commercial_realtime_protocol import (
    parse_room_subscription,
)


DOC = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "architecture"
    / "realtime-worklist.md"
)


def test_realtime_doc_covers_interaction_room_protocol() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "subscribe",
        "unsubscribe",
        "room:{uuid}",
        "room.message.created",
        "room.message.updated",
        "room.message.deleted",
        "room.reaction",
        "room.mention",
        "room.attachment",
        "accessDenied",
        "roomIdInvalid",
        "list_interaction_rooms",
        "/commercial/realtime/ws",
    )
    missing = [token for token in required if token not in text]
    assert not missing, f"doc missing protocol tokens: {missing}"


def test_protocol_helpers_match_documented_contract() -> None:
    assert interaction_room_key("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee") == (
        "room:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    )
    assert parse_room_subscription(
        '{"type":"subscribe","roomId":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}'
    ) == ("subscribe", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    assert parse_room_subscription(
        '{"type":"unsubscribe","room_id":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}'
    ) == ("unsubscribe", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    assert parse_room_subscription('{"type":"ping"}') is None
