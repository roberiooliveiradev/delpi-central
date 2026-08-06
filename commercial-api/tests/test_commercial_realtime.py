from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

from commercial_app.application.services.commercial_realtime_hub import CommercialRealtimeHub
from commercial_app.application.services.commercial_realtime_notify import (
    TEAM_ROOM,
    build_worklist_notification,
    notify_worklist_changed,
    user_room,
)


def test_hub_broadcasts_to_room():
    async def run() -> None:
        hub = CommercialRealtimeHub()
        loop = asyncio.get_running_loop()
        hub.bind_loop(loop)
        worker = asyncio.create_task(hub.worker())

        socket = AsyncMock()
        socket.send_json = AsyncMock()

        hub._rooms["user:seller-a"] = {socket}  # noqa: SLF001 — teste de hub

        await hub.broadcast_now("user:seller-a", {"type": "worklist.changed", "taskId": "1"})

        socket.send_json.assert_awaited_once()
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker

    asyncio.run(run())


def test_build_notification_mentions_who_assigned():
    note = build_worklist_notification(
        reason="task.reassigned",
        task_title="Ligar ACME",
        actor_display_name="Ana Gestora",
        audience="assignee",
    )
    assert note["title"] == "Tarefa reatribuída"
    assert note["message"] == "Ana Gestora atribuiu a você: Ligar ACME"
    assert note["variant"] == "info"


def test_build_notification_team_assignment_includes_assignee():
    note = build_worklist_notification(
        reason="task.created",
        task_title="Ligar ACME",
        actor_display_name="Ana Gestora",
        assignee_display_name="Bruno Vendedor",
        audience="team",
    )
    assert note["message"] == "Ana Gestora atribuiu a Bruno Vendedor: Ligar ACME"


def test_build_notification_completed_includes_actor():
    note = build_worklist_notification(
        reason="task.completed",
        task_title="Follow-up",
        actor_display_name="Usuário Comum",
        audience="team",
    )
    assert note["message"] == "Usuário Comum concluiu: Follow-up"


def test_notify_worklist_changed_schedules_user_and_team(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []

    def capture(room: str, payload: dict) -> None:
        scheduled.append((room, payload))

    hub.schedule_broadcast = capture
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.resolve_user_display_name",
        lambda _uid: "Ana Gestora",
    )

    notify_worklist_changed(
        reason="task.created",
        task_id="abc",
        assignee_user_ids=["seller-a"],
        actor_client_id="client-1",
        actor_user_id="manager-1",
        task_title="Ligar ACME",
    )

    by_room = {room: payload for room, payload in scheduled}
    assert user_room("seller-a") in by_room
    assert TEAM_ROOM in by_room

    # Mesmo payload em todas as salas — MFE personaliza «a você» pelo userId.
    for room, body in by_room.items():
        assert body["actorDisplayName"] == "Ana Gestora"
        assert body["assigneeUserIds"] == ["seller-a"]
        assert "Ana Gestora atribuiu" in body["notification"]["message"]
        assert body["notification"]["title"] == "Nova tarefa"


def test_notify_reassign_includes_previous_and_new_assignee(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )

    notify_worklist_changed(
        reason="task.reassigned",
        task_id="abc",
        assignee_user_ids=["seller-b", "seller-a"],
        actor_display_name="Ana Gestora",
        task_title="Follow-up",
    )

    by_room = {room: payload for room, payload in scheduled}
    assert set(by_room) == {TEAM_ROOM, user_room("seller-a"), user_room("seller-b")}
    body = by_room[user_room("seller-b")]
    assert body["assigneeUserIds"] == ["seller-b", "seller-a"]
    assert body["actorDisplayName"] == "Ana Gestora"
    assert "Ana Gestora reatribuiu" in body["notification"]["message"]


def test_user_room_key():
    assert user_room("seller-a") == "user:seller-a"
