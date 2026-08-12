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


def test_notify_portfolio_changed_schedules_member_rooms_only(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.resolve_user_display_name",
        lambda _uid: "Ana Gestora",
    )

    from commercial_app.application.services.commercial_realtime_notify import (
        notify_portfolio_changed,
    )
    from commercial_app.domain.services.seller_portfolio_messages_content_service import (
        SellerPortfolioMessagesContentService,
    )

    SellerPortfolioMessagesContentService.clear_cache()
    notify_portfolio_changed(
        reason="seller_portfolio.add_customer",
        portfolio_id="p1",
        member_user_ids=["seller-a", "helper-1"],
        display_name="Sul",
        actor_user_id="manager-1",
        actor_client_id="client-9",
    )

    by_room = {room: payload for room, payload in scheduled}
    assert set(by_room) == {user_room("seller-a"), user_room("helper-1")}
    assert TEAM_ROOM not in by_room
    body = by_room[user_room("seller-a")]
    assert body["type"] == "portfolio.changed"
    assert body["reason"] == "seller_portfolio.add_customer"
    assert body["portfolioId"] == "p1"
    assert body["displayName"] == "Sul"
    assert body["actorClientId"] == "client-9"
    assert body["notification"]["title"] == "Cliente vinculado"
    assert "Ana Gestora vinculou" in body["notification"]["message"]


def test_build_portfolio_notification_uses_json():
    from commercial_app.application.services.commercial_realtime_notify import (
        build_portfolio_notification,
    )
    from commercial_app.domain.services.seller_portfolio_messages_content_service import (
        SellerPortfolioMessagesContentService,
    )

    SellerPortfolioMessagesContentService.clear_cache()
    note = build_portfolio_notification(
        reason="seller_portfolio.deactivate",
        display_name="Norte",
        actor_display_name="Robério",
    )
    assert note["title"] == "Carteira inativada"
    assert note["message"] == "Robério inativou a carteira «Norte»."
    assert note["variant"] == "warning"


def test_resolve_user_display_name_never_uses_portfolio_label():
    from commercial_app.application.services import commercial_realtime_notify as notify

    assert notify.resolve_user_display_name(None) == "Alguém da equipe"
    assert notify.resolve_user_display_name("") == "Alguém da equipe"
    assert notify.resolve_user_display_name("helper-1") == "Alguém da equipe"
