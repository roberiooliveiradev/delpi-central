"""Tempo real do LNF — handshake, salas, emissão e log sem token."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from controllership_finance_app.application.invoice_posting.change_notifier import (
    SafeInvoicePostingChangeNotifier,
    configure_invoice_posting_realtime,
    lnf_realtime_should_mount,
    reset_invoice_posting_change_notifier,
    set_invoice_posting_change_notifier,
)
from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS,
    LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01,
)
from controllership_finance_app.application.invoice_posting.unmapped_supplier_product_service import (
    UnmappedSupplierProductRecorder,
)
from controllership_finance_app.application.invoice_posting.use_cases import (
    AddInvoicePostingCommentUseCase,
    BlockInvoicePostingRequestUseCase,
    CancelInvoicePostingRequestUseCase,
    CreateInvoicePostingRequestUseCase,
    PostManualInvoicePostingRequestUseCase,
    ResumeInvoicePostingRequestUseCase,
    RunInvoicePostingReconciliationUseCase,
    StartInvoicePostingRequestUseCase,
    UpdateInvoicePostingRequestUseCase,
)
from controllership_finance_app.infrastructure.invoice_posting.access_log_redaction import (
    install_token_redaction_filter,
    redact_token,
)
from controllership_finance_app.infrastructure.invoice_posting.realtime_hub import (
    InMemoryInvoicePostingRealtimeHub,
    get_invoice_posting_realtime_hub,
    set_invoice_posting_realtime_hub,
)
from controllership_finance_app.interface.http.routes.invoice_posting.realtime_routes import (
    router as realtime_router,
)
from tests.test_lancamento_notas_fiscais_reconciliation import (
    FakeRequests as ReconRequests,
)
from tests.test_lancamento_notas_fiscais_reconciliation import FakeSf1, _seed_request
from tests.test_lancamento_notas_fiscais_use_cases import (
    FakeRequests,
    FakeSuppliers,
    _creator,
    _manager,
    _payload,
    _processor,
)

PORTAL = "https://portal.example.com"
TOKEN = "lnf-test-token-do-not-log"
ROUTE = "controllership_finance_app.interface.http.routes.invoice_posting.realtime_routes"


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def request_changed(self, **kwargs) -> None:
        self.events.append(("request", kwargs))

    def queue_reconciled(self, **kwargs) -> None:
        self.events.append(("queue", kwargs))

    def unmapped_products_changed(self) -> None:
        self.events.append(("unmapped", {}))


class RaisingNotifier:
    def request_changed(self, **kwargs) -> None:
        raise RuntimeError("notify failed")

    def queue_reconciled(self, **kwargs) -> None:
        raise RuntimeError("notify failed")

    def unmapped_products_changed(self) -> None:
        raise RuntimeError("notify failed")


@pytest.fixture
def recorded():
    notifier = RecordingNotifier()
    set_invoice_posting_change_notifier(notifier)
    yield notifier
    reset_invoice_posting_change_notifier()


def _reasons(notifier: RecordingNotifier) -> list[str]:
    return [item[1]["reason"] for item in notifier.events if item[0] == "request"]


def _claims(exp: float | None = None) -> dict:
    return {"sub": "user-1", "exp": time.time() + 3600 if exp is None else exp}


def _rbac(permissions: list[str]):
    async def _load(_token: str) -> dict:
        return {
            "id": "user-1",
            "email": "user@example.com",
            "name": "Usuário",
            "permissions": permissions,
            "roles": [],
            "groups": [],
        }

    return _load


@pytest.fixture
def ws_client():
    configure_invoice_posting_realtime(enabled=True)
    app = FastAPI()
    app.include_router(realtime_router)
    with TestClient(app) as client:
        yield client
    reset_invoice_posting_change_notifier()
    set_invoice_posting_realtime_hub(None)


@contextmanager
def _connect(client: TestClient, token: str | None, permissions: list[str], *, exp=None, origin=PORTAL):
    patches = [
        patch(f"{ROUTE}.validate_token", return_value=_claims(exp)),
        patch(f"{ROUTE}.fastapi_auth.load_user_rbac", _rbac(permissions)),
    ]
    for item in patches:
        item.start()
    url = "/lancamento-notas-fiscais/realtime"
    if token is not None:
        url = f"{url}?token={token}"
    try:
        with client.websocket_connect(url, headers={"origin": origin}) as ws:
            yield ws
    finally:
        for item in patches:
            item.stop()


def test_t15_flags_off_do_not_mount() -> None:
    assert lnf_realtime_should_mount(hosted=False, realtime=True) is False
    assert lnf_realtime_should_mount(hosted=True, realtime=False) is False
    assert lnf_realtime_should_mount(hosted=False, realtime=False) is False
    assert lnf_realtime_should_mount(hosted=True, realtime=True) is True
    from controllership_finance_app.main import app

    paths = [getattr(route, "path", "") for route in app.routes]
    assert "/lancamento-notas-fiscais/realtime" not in paths


def test_t1_missing_token_closes_1008(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with _connect(ws_client, None, [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]):
            pass
    assert exc.value.code == 1008


def test_t2_invalid_token_closes_1008(ws_client) -> None:
    with patch(f"{ROUTE}.validate_token", side_effect=RuntimeError("bad")):
        with pytest.raises(WebSocketDisconnect) as exc:
            with ws_client.websocket_connect(
                f"/lancamento-notas-fiscais/realtime?token={TOKEN}",
                headers={"origin": PORTAL},
            ):
                pass
    assert exc.value.code == 1008


def test_t3_expired_token_closes_1008(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with _connect(
            ws_client,
            TOKEN,
            [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01],
            exp=time.time() - 10,
        ):
            pass
    assert exc.value.code == 1008


def test_t4_without_permission_closes_1008(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with _connect(ws_client, TOKEN, ["other.app.view"]):
            pass
    assert exc.value.code == 1008


def test_t5_foreign_origin_closes_1008(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with _connect(
            ws_client,
            TOKEN,
            [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01],
            origin="https://evil.example.com",
        ):
            pass
    assert exc.value.code == 1008


def test_t6_t7_t9_t14_room_errors_keep_the_socket(ws_client) -> None:
    missing = str(uuid4())
    other = str(uuid4())

    def lookup(request_id: str):
        if request_id == other:
            return "02"
        return None

    with patch(f"{ROUTE}.lookup_request_branch", lookup):
        with _connect(
            ws_client, TOKEN, [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]
        ) as ws:
            ws.send_json({"type": "subscribe", "room": "lnf:branch:02"})
            denied = ws.receive_json()
            assert denied == {
                "type": "error",
                "code": "forbidden_room",
                "room": "lnf:branch:02",
            }
            ws.send_json({"type": "subscribe", "room": f"lnf:request:{other}"})
            assert ws.receive_json()["code"] == "forbidden_room"
            ws.send_json({"type": "subscribe", "room": f"lnf:request:{missing}"})
            assert ws.receive_json()["code"] == "forbidden_room"
            ws.send_json({"type": "subscribe", "room": "lnf:branch:99"})
            assert ws.receive_json()["code"] == "unknown_room"
            ws.send_text("ping")
            assert ws.receive_json() == {"type": "pong"}


def test_t8_branch_02_event_does_not_reach_filial_01_socket(ws_client) -> None:
    hub = get_invoice_posting_realtime_hub()
    assert hub is not None
    with _connect(
        ws_client, TOKEN, [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]
    ) as ws:
        ws.send_json({"type": "subscribe", "room": "lnf:branch:01"})
        assert ws.receive_json()["type"] == "subscribed"
        hub.request_changed(
            branch="02",
            request_id=str(uuid4()),
            reason="created",
            actor_origin="user",
        )
        own_id = str(uuid4())
        hub.request_changed(
            branch="01",
            request_id=own_id,
            reason="updated",
            actor_origin="user",
        )
        event = ws.receive_json()
        assert event["branch"] == "01"
        assert event["requestId"] == own_id
        assert event["type"] == "lnf.request.changed"
        assert "supplier" not in event


def test_t13_closes_1000_at_exp_plus_grace(ws_client) -> None:
    hub = get_invoice_posting_realtime_hub()
    assert hub is not None

    async def _no_wait(_seconds: float) -> None:
        return None

    hub._sleep = _no_wait
    with pytest.raises(WebSocketDisconnect) as exc:
        with _connect(
            ws_client,
            TOKEN,
            [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01],
            exp=time.time() + 30,
        ) as ws:
            ws.receive_text()
    assert exc.value.code == 1000


def test_t16_sync_emit_reaches_the_socket(ws_client) -> None:
    hub = get_invoice_posting_realtime_hub()
    assert hub is not None
    with _connect(
        ws_client, TOKEN, [LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]
    ) as ws:
        ws.send_json({"type": "subscribe", "room": "lnf:branch:01"})
        assert ws.receive_json()["type"] == "subscribed"
        hub.request_changed(
            branch="01",
            request_id="11111111-1111-1111-1111-111111111111",
            reason="created",
            actor_origin="user",
        )
        event = ws.receive_json()
        assert event["reason"] == "created"
        assert event["actorOrigin"] == "user"


def test_t17_log_redacts_token(caplog) -> None:
    install_token_redaction_filter()
    access = logging.getLogger("uvicorn.access")
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        access.info(
            '%s - "%s %s HTTP/%s" %d',
            "127.0.0.1",
            "GET",
            f"/lancamento-notas-fiscais/realtime?token={TOKEN}",
            "1.1",
            101,
        )
    assert TOKEN not in caplog.text
    assert "token=[REDACTED]" in caplog.text
    assert redact_token(f"token={TOKEN}&x=1") == "token=[REDACTED]&x=1"


def test_uvicorn_access_path_includes_the_query() -> None:
    from uvicorn.protocols.http.httptools_impl import get_path_with_query_string

    scope = {
        "path": "/lancamento-notas-fiscais/realtime",
        "query_string": f"token={TOKEN}".encode(),
    }
    rendered = get_path_with_query_string(scope)
    if isinstance(rendered, bytes):
        rendered = rendered.decode()
    assert TOKEN in rendered
    assert TOKEN not in redact_token(rendered)


def test_t10_writes_emit_the_contract_reasons(recorded) -> None:
    with patch.multiple(
        "controllership_finance_app.application.invoice_posting.use_cases",
        notify_block_assignee=lambda **_kwargs: None,
        notify_block_resolved=lambda **_kwargs: None,
        notify_comment_mentions=lambda **_kwargs: None,
    ):
        _assert_write_reasons(recorded)


def _assert_write_reasons(recorded) -> None:
    repo = FakeRequests()
    created = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(), _creator()
    )
    UpdateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        created["id"], {"observation": "alterado"}, _creator()
    )
    StartInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    BlockInvoicePostingRequestUseCase(repo).execute(
        created["id"],
        actor=_processor(),
        block_reason="other",
        block_description="pendência",
        assignee_user_id="u-compras",
        assignee_name="Compras",
    )
    ResumeInvoicePostingRequestUseCase(repo).execute(created["id"], _processor())
    AddInvoicePostingCommentUseCase(repo).execute(
        created["id"], actor=_creator(), body="um comentário"
    )
    CancelInvoicePostingRequestUseCase(repo).execute(
        created["id"], actor=_manager(), justification="não vou lançar"
    )
    posted = CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
        _payload(document="222"), _creator()
    )
    PostManualInvoicePostingRequestUseCase(repo).execute(
        posted["id"], actor=_processor(), justification="lançada"
    )
    assert _reasons(recorded) == [
        "created",
        "updated",
        "status_changed",
        "status_changed",
        "status_changed",
        "comment_added",
        "cancelled",
        "created",
        "manual_posted",
    ]


def test_t10_purchase_order_link_emits(recorded) -> None:
    from tests.test_lancamento_notas_fiscais_use_cases import (
        _ScopedOpenOrders,
        _open_line,
    )

    repo = FakeRequests()
    orders = _ScopedOpenOrders([_open_line("654321", "0001")])
    CreateInvoicePostingRequestUseCase(repo, FakeSuppliers(), orders).execute(
        {
            **_payload(),
            "linked_purchase_orders": [
                {
                    "order_number": "654321",
                    "delivery_date": "2026-10-10",
                    "lines": [{"order_item": "0001"}],
                }
            ],
        },
        _creator(),
    )
    assert _reasons(recorded) == ["created", "purchase_order_linked"]


def test_t11_rolled_back_create_emits_nothing(recorded) -> None:
    repo = FakeRequests(fail_history_once=True)
    with pytest.raises(RuntimeError):
        CreateInvoicePostingRequestUseCase(repo, FakeSuppliers()).execute(
            _payload(), _creator()
        )
    assert recorded.events == []


def test_t12_notifier_exception_does_not_change_the_result() -> None:
    set_invoice_posting_change_notifier(
        SafeInvoicePostingChangeNotifier(RaisingNotifier())
    )
    try:
        created = CreateInvoicePostingRequestUseCase(
            FakeRequests(), FakeSuppliers()
        ).execute(_payload(), _creator())
    finally:
        reset_invoice_posting_change_notifier()
    assert created["status"] == "pending"


def _sf1_for(row: dict) -> dict:
    return {
        "branch_code": row["branch_code"],
        "supplier_code": row["supplier_code"],
        "supplier_store": row["supplier_store"],
        "document_match_key": row["document_match_key"],
        "series": row["series"],
        "sf1_recno": 10,
        "erp_entry_date_raw": "20260724",
    }


def test_t18_queue_event_only_for_branches_with_matches(recorded) -> None:
    none = _seed_request(branch_code="01", document="100")
    one = _seed_request(branch_code="01", document="101")
    two = _seed_request(branch_code="02", document="102")
    repo = ReconRequests([none, one, two])
    RunInvoicePostingReconciliationUseCase(repo, FakeSf1([])).execute_batch()
    assert recorded.events == []

    recorded.events.clear()
    repo = ReconRequests(
        [
            _seed_request(branch_code="01", document="201"),
            _seed_request(branch_code="02", document="202"),
        ]
    )
    rows = list(repo.rows.values())
    RunInvoicePostingReconciliationUseCase(
        repo, FakeSf1([_sf1_for(row) for row in rows])
    ).execute_batch()
    queues = [item for item in recorded.events if item[0] == "queue"]
    assert {item[1]["branch"] for item in queues} == {"01", "02"}
    assert all(item[1]["updated_count"] > 0 for item in queues)
    reconciled = [
        item[1]["reason"]
        for item in recorded.events
        if item[0] == "request"
    ]
    assert reconciled == ["reconciled", "reconciled"]


def test_t10_unmapped_emits_only_when_insert_persists(recorded) -> None:
    class _Items:
        def execute(self, **_kwargs):
            return {"items": []}

    class _Repo:
        def __init__(self, count: int) -> None:
            self.count = count

        def insert_unmapped_supplier_products(self, rows):
            return self.count if rows else 0

    with patch(
        "controllership_finance_app.application.invoice_posting.unmapped_supplier_product_service.unmapped_product_rows",
        return_value=[{"request_id": "x"}],
    ), patch(
        "controllership_finance_app.application.invoice_posting.unmapped_supplier_product_service.notify_unmapped_supplier_products"
    ):
        UnmappedSupplierProductRecorder(items=_Items(), requests=_Repo(0)).record(
            authorization="Bearer x",
            document_id="aabbccddeeff001122334455",
            provider_entity_id="p",
            access_key="3" * 44,
            branch="01",
            supplier_code="000001",
            supplier_store="01",
            supplier_name="Fornecedor",
            document_number="1",
            series="1",
            request_id=str(uuid4()),
        )
        assert recorded.events == []
        UnmappedSupplierProductRecorder(items=_Items(), requests=_Repo(1)).record(
            authorization="Bearer x",
            document_id="aabbccddeeff001122334455",
            provider_entity_id="p",
            access_key="3" * 44,
            branch="01",
            supplier_code="000001",
            supplier_store="01",
            supplier_name="Fornecedor",
            document_number="1",
            series="1",
            request_id=str(uuid4()),
        )
    assert recorded.events == [("unmapped", {})]


def test_review_unmapped_cannot_subscribe_a_branch(ws_client) -> None:
    with _connect(
        ws_client, TOKEN, [LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS]
    ) as ws:
        ws.send_json({"type": "subscribe", "room": "lnf:branch:01"})
        assert ws.receive_json()["code"] == "forbidden_room"
        ws.send_json({"type": "subscribe", "room": "lnf:unmapped-products"})
        assert ws.receive_json()["type"] == "subscribed"


def test_slow_socket_is_removed_without_blocking_the_other() -> None:
    import asyncio

    class _Socket:
        def __init__(self, *, fail: bool) -> None:
            self.fail = fail
            self.messages: list[dict] = []

        async def send_json(self, payload):
            if self.fail:
                raise RuntimeError("slow")
            self.messages.append(payload)

        async def close(self, code=1000):
            self.closed = code

    async def _run():
        hub = InMemoryInvoicePostingRealtimeHub()
        good = _Socket(fail=False)
        bad = _Socket(fail=True)
        hub._rooms["lnf:branch:01"] = {good, bad}
        hub._socket_rooms[good] = {"lnf:branch:01"}
        hub._socket_rooms[bad] = {"lnf:branch:01"}
        await hub.broadcast_now(["lnf:branch:01"], {"type": "lnf.request.changed"})
        return good, bad, hub

    good, bad, hub = asyncio.run(_run())
    assert good.messages
    assert bad not in hub._socket_rooms
