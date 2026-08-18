from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

from commercial_app.application.services.commercial_realtime_notify import (
    mentioned_user_ids_from_message,
    notify_interaction_mention,
    user_room,
)
from commercial_app.domain.entities.interaction_room import (
    InteractionMention,
    InteractionMessage,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


def setup_function() -> None:
    InteractionRoomContentService.clear_cache()


def _message(*, mentions=()) -> InteractionMessage:
    return InteractionMessage(
        id=UUID("00000000-0000-0000-0000-000000000222"),
        room_id=UUID("00000000-0000-0000-0000-000000000111"),
        message_kind="text",
        body_text="Preciso que o @Joao confirme o pedido 102942.",
        created_at=datetime.now(timezone.utc),
        author_user_id="author-1",
        mentions=tuple(mentions),
    )


def test_mentioned_user_ids_ignores_objects() -> None:
    msg = _message(
        mentions=(
            InteractionMention(
                id=UUID("00000000-0000-0000-0000-000000000301"),
                message_id=UUID("00000000-0000-0000-0000-000000000222"),
                mention_kind="user",
                ref={"user_id": "u2"},
                label="@Joao",
            ),
            InteractionMention(
                id=UUID("00000000-0000-0000-0000-000000000302"),
                message_id=UUID("00000000-0000-0000-0000-000000000222"),
                mention_kind="order",
                ref={"branch": "01", "order": "102942"},
                label="@102942",
            ),
        )
    )
    assert mentioned_user_ids_from_message(msg) == ["u2"]


def test_notify_interaction_mention_ws_and_portal_offline(monkeypatch) -> None:
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    hub.is_user_online = lambda uid: uid == "online-user"
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    monkeypatch.setattr(
        "commercial_app.application.services.task_portal_notification_delivery_policy.commercial_realtime_hub",
        hub,
    )

    portal_calls: list[dict] = []

    class _Portal:
        def notify_interaction_mention(self, **kwargs):
            portal_calls.append(kwargs)
            return True

    msg = _message(
        mentions=(
            InteractionMention(
                id=UUID("00000000-0000-0000-0000-000000000301"),
                message_id=UUID("00000000-0000-0000-0000-000000000222"),
                mention_kind="user",
                ref={"user_id": "online-user"},
                label="@Online",
            ),
            InteractionMention(
                id=UUID("00000000-0000-0000-0000-000000000304"),
                message_id=UUID("00000000-0000-0000-0000-000000000222"),
                mention_kind="user",
                ref={"user_id": "offline-user"},
                label="@Offline",
            ),
            InteractionMention(
                id=UUID("00000000-0000-0000-0000-000000000305"),
                message_id=UUID("00000000-0000-0000-0000-000000000222"),
                mention_kind="user",
                ref={"user_id": "author-1"},
                label="@Self",
            ),
        )
    )
    notify_interaction_mention(
        message=msg,
        actor_user_id="author-1",
        actor_display_name="Ana",
        portal=_Portal(),
    )

    rooms = {room for room, _ in scheduled}
    assert rooms == {user_room("online-user"), user_room("offline-user")}
    payload = scheduled[0][1]
    assert payload["type"] == "room.mention"
    assert set(payload["mentionedUserIds"]) == {"online-user", "offline-user"}
    assert "Ana" in payload["notification"]["message"]

    assert len(portal_calls) == 1
    assert portal_calls[0]["user_ids"] == ["offline-user"]
    assert portal_calls[0]["room_id"] == str(msg.room_id)


def test_notify_interaction_mention_portal_category(monkeypatch) -> None:
    captured: dict = {}

    class _Resp:
        status_code = 200
        text = "ok"

    def _post(url, *, headers, json, timeout):
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr(
        "commercial_app.application.services.commercial_portal_notification_service.httpx.post",
        _post,
    )
    from commercial_app.application.services.commercial_portal_notification_service import (
        CommercialPortalNotificationService,
    )

    svc = CommercialPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="secret",
        enabled=True,
    )
    assert svc.notify_interaction_mention(
        user_ids=["u2"],
        room_id="111",
        message_id="222",
        actor_display_name="Ana",
        excerpt="oi",
    )
    body = captured["json"]
    assert body["category"] == "commercial_collaboration"
    assert body["metadata"]["event"] == InteractionRoomContentService.mention_event_type()
    assert "/apps/commercial/interaction-rooms/111" in body["action"]["target"]


def test_content_notifications_section() -> None:
    assert InteractionRoomContentService.mention_category() == "commercial_collaboration"
    assert "mencionou" in InteractionRoomContentService.format_mention_message(
        actor="Ana",
        excerpt="teste",
    )
