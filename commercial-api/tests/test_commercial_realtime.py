from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

from starlette.websockets import WebSocketDisconnect

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


def test_hub_presence_multi_tab_counts_as_one_online():
    async def run() -> None:
        hub = CommercialRealtimeHub()

        async def connect_and_hold(
            ws: AsyncMock, *, user_id: str, rooms: list[str]
        ) -> tuple[asyncio.Event, asyncio.Task]:
            released = asyncio.Event()

            async def wait_release():
                await released.wait()
                raise WebSocketDisconnect()

            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.receive_text = AsyncMock(side_effect=wait_release)
            task = asyncio.create_task(
                hub.connect(ws, room_keys=rooms, user_id=user_id, client_id=user_id)
            )
            await asyncio.sleep(0)
            return released, task

        manager = AsyncMock()
        seller_a = AsyncMock()
        seller_b = AsyncMock()

        m_release, m_task = await connect_and_hold(
            manager, user_id="manager-1", rooms=[TEAM_ROOM, "user:manager-1"]
        )
        assert hub.online_user_ids() == ["manager-1"]
        snapshot = [
            call.args[0]
            for call in manager.send_json.await_args_list
            if isinstance(call.args[0], dict) and call.args[0].get("type") == "presence.updated"
        ]
        assert snapshot and snapshot[0]["onlineUserIds"] == ["manager-1"]

        a1_release, a1_task = await connect_and_hold(
            seller_a, user_id="seller-a", rooms=["user:seller-a"]
        )
        a2_release, a2_task = await connect_and_hold(
            seller_b, user_id="seller-a", rooms=["user:seller-a"]
        )
        assert hub.online_user_ids() == ["manager-1", "seller-a"]

        presence_fanout = [
            call.args[0]
            for call in manager.send_json.await_args_list
            if isinstance(call.args[0], dict)
            and call.args[0].get("type") == "presence.updated"
            and "seller-a" in (call.args[0].get("onlineUserIds") or [])
        ]
        assert presence_fanout

        a1_release.set()
        await a1_task
        assert "seller-a" in hub.online_user_ids()

        a2_release.set()
        await a2_task
        assert "seller-a" not in hub.online_user_ids()
        assert hub.online_user_ids() == ["manager-1"]

        m_release.set()
        await m_task
        assert hub.online_user_ids() == []

    asyncio.run(run())


def test_hub_presence_idle_timeout_marks_offline():
    async def run() -> None:
        hub = CommercialRealtimeHub(idle_seconds=0.05)

        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()

        async def hang_forever():
            await asyncio.sleep(10)

        ws.receive_text = hang_forever

        task = asyncio.create_task(
            hub.connect(
                ws,
                room_keys=["user:seller-a"],
                user_id="seller-a",
                client_id="c1",
            )
        )
        await asyncio.sleep(0.01)
        assert hub.online_user_ids() == ["seller-a"]
        await asyncio.wait_for(task, timeout=1.0)
        assert hub.online_user_ids() == []
        ws.close.assert_awaited()

    asyncio.run(run())


def test_hub_subscribe_join_and_unsubscribe_room():
    async def run() -> None:
        from uuid import uuid4

        from commercial_app.application.services.commercial_realtime_notify import (
            interaction_room_key,
        )
        from commercial_app.application.services.commercial_realtime_protocol import (
            handle_realtime_client_message,
        )

        hub = CommercialRealtimeHub()
        room_id = str(uuid4())
        room_key = interaction_room_key(room_id)
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        hub._socket_meta[ws] = (("user:seller-a",), "seller-a")  # noqa: SLF001
        hub._rooms["user:seller-a"] = {ws}  # noqa: SLF001

        ack = await handle_realtime_client_message(
            hub=hub,
            websocket=ws,
            user_id="seller-a",
            raw='{"type":"subscribe","roomId":"%s"}' % room_id,
            can_join_room=lambda _uid, rid: rid == room_id,
        )
        assert ack is not None
        assert ack["type"] == "subscribed"
        assert room_key in hub.socket_room_keys(ws)
        assert ws in hub._rooms.get(room_key, set())  # noqa: SLF001

        ack = await handle_realtime_client_message(
            hub=hub,
            websocket=ws,
            user_id="seller-a",
            raw='{"type":"unsubscribe","roomId":"%s"}' % room_id,
            can_join_room=lambda _uid, rid: rid == room_id,
        )
        assert ack is not None
        assert ack["type"] == "unsubscribed"
        assert room_key not in hub.socket_room_keys(ws)

    asyncio.run(run())


def test_subscribe_denied_without_membership():
    async def run() -> None:
        from uuid import uuid4

        from commercial_app.application.services.commercial_realtime_notify import (
            interaction_room_key,
        )
        from commercial_app.application.services.commercial_realtime_protocol import (
            handle_realtime_client_message,
        )

        hub = CommercialRealtimeHub()
        room_id = str(uuid4())
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        hub._socket_meta[ws] = (("user:seller-a",), "seller-a")  # noqa: SLF001
        hub._rooms["user:seller-a"] = {ws}  # noqa: SLF001
        ack = await handle_realtime_client_message(
            hub=hub,
            websocket=ws,
            user_id="seller-a",
            raw='{"type":"subscribe","roomId":"%s"}' % room_id,
            can_join_room=lambda *_args: False,
        )
        assert ack is not None
        assert ack["type"] == "error"
        assert ack["code"] == "accessDenied"
        assert interaction_room_key(room_id) not in hub.socket_room_keys(ws)

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


def test_notify_ready_to_invoice_changed_schedules_user_and_team(monkeypatch):
    from commercial_app.application.services.commercial_realtime_notify import (
        notify_ready_to_invoice_changed,
    )

    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []

    def capture(room: str, payload: dict) -> None:
        scheduled.append((room, payload))

    hub.schedule_broadcast = capture
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )

    notify_ready_to_invoice_changed(
        user_ids=["seller-a"],
        line_key="01|10|01",
        pedido="10",
        linha="01",
        cliente="ACME",
        filial="01",
    )

    by_room = {room: payload for room, payload in scheduled}
    assert user_room("seller-a") in by_room
    assert TEAM_ROOM in by_room
    body = by_room[TEAM_ROOM]
    assert body["type"] == "orders.ready_to_invoice"
    assert body["pedido"] == "10"
    assert "pronto para faturar" in body["notification"]["title"].lower()
    assert "view=board" not in (body.get("actionTarget") or "")


def test_notify_ready_to_invoice_team_room_without_user_ids(monkeypatch):
    """Billing-only recipients: still toast gestores on TEAM_ROOM."""
    from commercial_app.application.services.commercial_realtime_notify import (
        notify_ready_to_invoice_changed,
    )

    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )

    notify_ready_to_invoice_changed(
        user_ids=[],
        line_key="01|10|01",
        pedido="10",
        linha="01",
        cliente="ACME",
        filial="01",
    )

    by_room = {room: payload for room, payload in scheduled}
    assert set(by_room) == {TEAM_ROOM}
    assert by_room[TEAM_ROOM]["type"] == "orders.ready_to_invoice"


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


def test_notify_portfolio_changed_schedules_member_and_team_rooms(monkeypatch):
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
    assert set(by_room) == {TEAM_ROOM, user_room("seller-a"), user_room("helper-1")}
    body = by_room[user_room("seller-a")]
    assert body["type"] == "portfolio.changed"
    assert body["reason"] == "seller_portfolio.add_customer"
    assert body["portfolioId"] == "p1"
    assert body["displayName"] == "Sul"
    assert body["actorClientId"] == "client-9"
    assert body["notification"]["title"] == "Cliente vinculado"
    assert "Ana Gestora vinculou" in body["notification"]["message"]
    assert by_room[TEAM_ROOM]["portfolioId"] == "p1"


def test_notify_account_changed_schedules_member_and_team_rooms(monkeypatch):
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
        notify_account_changed,
    )
    from commercial_app.domain.services.audit_messages_content_service import (
        AuditMessagesContentService,
    )

    AuditMessagesContentService.clear_cache()
    notify_account_changed(
        reason="account.contact.created",
        customer_code="000001",
        customer_store="01",
        member_user_ids=["seller-a"],
        actor_user_id="manager-1",
        actor_display_name="Ana Gestora",
        actor_client_id="client-9",
        payload={"full_name": "Ana Souza", "channel": "whatsapp"},
    )

    by_room = {room: payload for room, payload in scheduled}
    assert set(by_room) == {TEAM_ROOM, user_room("seller-a"), user_room("manager-1")}
    body = by_room[user_room("seller-a")]
    assert body["type"] == "account.changed"
    assert body["reason"] == "account.contact.created"
    assert body["customerCode"] == "000001"
    assert body["customerStore"] == "01"
    assert body["actorClientId"] == "client-9"
    assert body["notification"]["title"] == "Contato criado"
    assert "Ana Gestora" in body["notification"]["message"]
    assert by_room[TEAM_ROOM]["customerCode"] == "000001"


def test_member_user_ids_for_customer():
    from types import SimpleNamespace

    from commercial_app.application.services.commercial_realtime_notify import (
        member_user_ids_for_customer,
    )

    portfolios = [
        SimpleNamespace(
            active=True,
            user_id="owner-1",
            customers=[
                SimpleNamespace(customer_code="10", customer_store="01"),
            ],
            members=[
                SimpleNamespace(user_id="owner-1", role="owner"),
                SimpleNamespace(user_id="helper-1", role="member"),
            ],
        ),
        SimpleNamespace(
            active=True,
            user_id="other",
            customers=[
                SimpleNamespace(customer_code="99", customer_store="01"),
            ],
            members=[SimpleNamespace(user_id="other", role="owner")],
        ),
    ]
    assert member_user_ids_for_customer(
        portfolios,
        customer_code="10",
        customer_store="01",
    ) == ["owner-1", "helper-1"]


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


def test_notify_interaction_attachment_schedules_member_rooms(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.resolve_user_display_name",
        lambda _uid: "Ana",
    )
    from commercial_app.application.services.commercial_realtime_notify import (
        INTERACTION_HUB_ROOM,
        interaction_room_key,
        notify_interaction_attachment,
        user_room,
    )

    notify_interaction_attachment(
        room_id="r1",
        message_id="m1",
        attachment_id="a1",
        file_name="proposta.pdf",
        member_user_ids=["u1", "u2"],
        actor_user_id="u1",
        actor_display_name="Ana",
        reason="uploaded",
    )
    rooms = {room for room, _ in scheduled}
    assert interaction_room_key("r1") in rooms
    assert INTERACTION_HUB_ROOM in rooms
    assert user_room("u1") in rooms
    assert user_room("u2") in rooms
    body = next(
        payload
        for _room, payload in scheduled
        if payload["type"] == "room.attachment" and payload.get("notification")
    )
    assert body["type"] == "room.attachment"
    assert body["reason"] == "attachment.uploaded"
    assert "proposta.pdf" in body["notification"]["message"]


def test_notify_room_message_fanout_to_interaction_room(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    from commercial_app.application.services.commercial_realtime_notify import (
        interaction_room_key,
        notify_room_message_changed,
        notify_room_reaction_changed,
    )
    from commercial_app.domain.entities.interaction_room import InteractionMessage
    from datetime import datetime, timezone
    from uuid import UUID

    message = InteractionMessage(
        id=UUID("00000000-0000-0000-0000-000000000222"),
        room_id=UUID("00000000-0000-0000-0000-000000000111"),
        message_kind="text",
        body_text="olá",
        created_at=datetime.now(timezone.utc),
        author_user_id="u1",
    )
    notify_room_message_changed(
        reason="created",
        room_id=str(message.room_id),
        message=message,
        actor_user_id="u1",
        actor_display_name="Ana",
    )
    assert len(scheduled) == 1
    room, payload = scheduled[0]
    assert room == interaction_room_key(str(message.room_id))
    assert payload["type"] == "room.message.created"
    assert payload["message"]["body_text"] == "olá"

    scheduled.clear()
    notify_room_reaction_changed(
        room_id=str(message.room_id),
        message_id=str(message.id),
        code="ok",
        actor_user_id="u2",
        action="set",
    )
    assert scheduled[0][0] == interaction_room_key(str(message.room_id))
    assert scheduled[0][1]["type"] == "room.reaction"
    assert scheduled[0][1]["action"] == "set"


def test_notify_interaction_room_activity_includes_inbox(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    from commercial_app.application.services.commercial_realtime_notify import (
        INTERACTION_HUB_ROOM,
        interaction_room_key,
        notify_interaction_room_activity,
        notify_room_pin_changed,
    )
    from commercial_app.domain.entities.interaction_room import InteractionMessage
    from datetime import datetime, timezone
    from uuid import UUID

    message = InteractionMessage(
        id=UUID("00000000-0000-0000-0000-000000000222"),
        room_id=UUID("00000000-0000-0000-0000-000000000111"),
        message_kind="text",
        body_text="olá",
        created_at=datetime.now(timezone.utc),
        author_user_id="u1",
    )
    notify_interaction_room_activity(
        reason="created",
        room_id=str(message.room_id),
        message=message,
        actor_user_id="u1",
    )
    rooms = {room for room, _ in scheduled}
    assert interaction_room_key(str(message.room_id)) in rooms
    assert INTERACTION_HUB_ROOM in rooms
    inbox = next(p for r, p in scheduled if p["type"] == "room.inbox.changed")
    assert inbox["roomId"] == str(message.room_id)

    scheduled.clear()
    notify_room_pin_changed(
        room_id=str(message.room_id),
        message_id=str(message.id),
        action="set",
        actor_user_id="u1",
    )
    types = {payload["type"] for _room, payload in scheduled}
    assert "room.pin" in types
    assert "room.inbox.changed" in types


def test_notify_room_updated_broadcasts_thread_and_inbox(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []
    hub.schedule_broadcast = lambda room, payload: scheduled.append((room, payload))
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )
    from commercial_app.application.services.commercial_realtime_notify import (
        INTERACTION_HUB_ROOM,
        interaction_room_key,
        notify_room_updated,
    )

    notify_room_updated(
        room_id="00000000-0000-0000-0000-000000000111",
        title="Pedido 12345",
        actor_user_id="u1",
        actor_display_name="Ana",
        actor_client_id="client-a",
    )
    rooms = {room for room, _ in scheduled}
    rid = "00000000-0000-0000-0000-000000000111"
    assert interaction_room_key(rid) in rooms
    assert INTERACTION_HUB_ROOM in rooms
    updated = next(p for _, p in scheduled if p["type"] == "room.updated")
    assert updated["roomId"] == rid
    assert updated["title"] == "Pedido 12345"
    assert updated["actorClientId"] == "client-a"


def test_realtime_handshake_joins_interaction_hub() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "commercial_app"
        / "interface"
        / "http"
        / "routes"
        / "realtime_routes.py"
    ).read_text(encoding="utf-8")
    assert "INTERACTION_HUB_ROOM" in source
    assert "room_keys = [user_room(user_id), INTERACTION_HUB_ROOM]" in source
