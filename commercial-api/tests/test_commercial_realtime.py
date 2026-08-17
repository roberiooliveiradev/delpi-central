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
    assert "Pronto para faturar" in body["notification"]["title"]
    assert "view=board" not in (body.get("actionTarget") or "")


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
