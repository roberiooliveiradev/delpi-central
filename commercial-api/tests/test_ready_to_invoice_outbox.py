"""Outbox enqueue/publish for ready_to_invoice notifications."""

from __future__ import annotations

from commercial_app.application.services.commercial_portal_notification_service import (
    CommercialPortalNotificationService,
)
from commercial_app.application.use_cases.detect_ready_to_invoice_entries import (
    DetectReadyToInvoiceResult,
    ReadyToInvoiceEntry,
)
from commercial_app.application.use_cases.enqueue_ready_to_invoice_notifications import (
    EnqueueReadyToInvoiceNotificationsUseCase,
    PublishIntegrationOutboxUseCase,
)
from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationOutboxRow,
)
from commercial_app.domain.services.ready_to_invoice_recipient_resolver_service import (
    ReadyToInvoiceRecipients,
)


class _OutboxMemory:
    def __init__(self) -> None:
        self.rows: list[IntegrationOutboxRow] = []
        self.published: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def enqueue(self, *, event_type, aggregate_type, aggregate_id, payload):
        row = IntegrationOutboxRow(
            id=f"ob-{len(self.rows)+1}",
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            created_at=None,
            available_at=None,
            published_at=None,
            attempts=0,
            last_error=None,
        )
        self.rows.append(row)
        return row

    def list_pending(self, *, limit: int = 50):
        return [row for row in self.rows if row.id not in self.published][:limit]

    def mark_published(self, outbox_id: str) -> None:
        self.published.append(outbox_id)

    def mark_failed(self, outbox_id: str, *, error: str) -> None:
        self.failed.append((outbox_id, error))


class _DetectStub:
    def __init__(self, result: DetectReadyToInvoiceResult) -> None:
        self._result = result

    def execute(self, *, persist_snapshot: bool = True) -> DetectReadyToInvoiceResult:
        return self._result


def test_enqueue_writes_outbox_with_deep_link() -> None:
    outbox = _OutboxMemory()
    detection = DetectReadyToInvoiceResult(
        previous_key_count=0,
        current_key_count=1,
        entered=(
            ReadyToInvoiceEntry(
                line_key="01|10|01",
                item={
                    "pedido": "10",
                    "linha": "01",
                    "nome_cliente": "ACME",
                    "filial": "01",
                },
                recipients=ReadyToInvoiceRecipients(
                    seller_user_ids=frozenset({"u1"}),
                    billing_user_ids=frozenset(),
                    billing_permission_codes=("commercial.billing.notify",),
                ),
            ),
        ),
        board_deep_link_path="/apps/commercial/open-orders?stage=ready_to_invoice",
    )
    result = EnqueueReadyToInvoiceNotificationsUseCase(
        detect=_DetectStub(detection),  # type: ignore[arg-type]
        outbox=outbox,
    ).execute()
    assert result.enqueued == 1
    assert len(outbox.rows) == 1
    payload = outbox.rows[0].payload
    assert payload["userIds"] == ["u1"]
    assert payload["permissionCodes"] == ["commercial.billing.notify"]
    assert "stage=ready_to_invoice" in payload["actionTarget"]
    assert "view=board" not in payload["actionTarget"]
    assert "q=10" in payload["actionTarget"]
    assert "branch=01" in payload["actionTarget"]


def test_publish_calls_portal_notifier(monkeypatch) -> None:
    outbox = _OutboxMemory()
    outbox.enqueue(
        event_type="commercial.order.ready_to_invoice",
        aggregate_type="open_order_line",
        aggregate_id="01|10|01",
        payload={
            "lineKey": "01|10|01",
            "userIds": ["u1"],
            "permissionCodes": [],
            "actionTarget": "/apps/commercial/open-orders?stage=ready_to_invoice&q=10&branch=01",
            "pedido": "10",
            "linha": "01",
            "cliente": "ACME",
            "filial": "01",
        },
    )
    calls: list[dict] = []

    class _Notifier(CommercialPortalNotificationService):
        def __init__(self) -> None:
            super().__init__(enabled=True, service_token="tok")

        def notify_ready_to_invoice(self, **kwargs):  # type: ignore[override]
            calls.append(kwargs)
            return True

    result = PublishIntegrationOutboxUseCase(
        outbox=outbox,
        notifier=_Notifier(),
    ).execute()
    assert result.published == 1
    assert outbox.published == ["ob-1"]
    assert calls[0]["line_key"] == "01|10|01"
    assert calls[0]["user_ids"] == ["u1"]
    assert "ready_to_invoice" in calls[0]["action_target"]
    assert "view=board" not in calls[0]["action_target"]


def test_publish_skips_portal_for_online_user_ids(monkeypatch) -> None:
    from commercial_app.application.services import (
        task_portal_notification_delivery_policy as policy_mod,
    )

    class _Hub:
        def is_user_online(self, user_id: str | None) -> bool:
            return str(user_id or "") == "online-user"

    monkeypatch.setattr(
        policy_mod,
        "commercial_realtime_hub",
        _Hub(),
    )
    outbox = _OutboxMemory()
    outbox.enqueue(
        event_type="commercial.order.ready_to_invoice",
        aggregate_type="open_order_line",
        aggregate_id="01|10|01",
        payload={
            "lineKey": "01|10|01",
            "userIds": ["online-user", "offline-user"],
            "permissionCodes": [],
            "actionTarget": "/apps/commercial/open-orders?stage=ready_to_invoice",
            "pedido": "10",
            "linha": "01",
            "cliente": "ACME",
            "filial": "01",
        },
    )
    calls: list[dict] = []

    class _Notifier(CommercialPortalNotificationService):
        def __init__(self) -> None:
            super().__init__(enabled=True, service_token="tok")

        def notify_ready_to_invoice(self, **kwargs):  # type: ignore[override]
            calls.append(kwargs)
            return True

    result = PublishIntegrationOutboxUseCase(
        outbox=outbox,
        notifier=_Notifier(),
    ).execute()
    assert result.published == 1
    assert calls[0]["user_ids"] == ["offline-user"]


def test_publish_acks_when_all_user_ids_online_and_no_permissions(monkeypatch) -> None:
    from commercial_app.application.services import (
        task_portal_notification_delivery_policy as policy_mod,
    )
    from commercial_app.application.services import commercial_realtime_notify as notify_mod

    class _Hub:
        def is_user_online(self, user_id: str | None) -> bool:
            return True

    monkeypatch.setattr(policy_mod, "commercial_realtime_hub", _Hub())
    ws_calls: list[dict] = []

    def _capture_r2i(**kwargs):
        ws_calls.append(kwargs)

    monkeypatch.setattr(notify_mod, "notify_ready_to_invoice_changed", _capture_r2i)
    outbox = _OutboxMemory()
    outbox.enqueue(
        event_type="commercial.order.ready_to_invoice",
        aggregate_type="open_order_line",
        aggregate_id="01|10|01",
        payload={
            "lineKey": "01|10|01",
            "userIds": ["online-user"],
            "permissionCodes": [],
            "actionTarget": "/apps/commercial/open-orders?stage=ready_to_invoice",
            "pedido": "10",
            "linha": "01",
            "cliente": "ACME",
            "filial": "01",
        },
    )
    calls: list[dict] = []

    class _Notifier(CommercialPortalNotificationService):
        def __init__(self) -> None:
            super().__init__(enabled=True, service_token="tok")

        def notify_ready_to_invoice(self, **kwargs):  # type: ignore[override]
            calls.append(kwargs)
            return True

    result = PublishIntegrationOutboxUseCase(
        outbox=outbox,
        notifier=_Notifier(),
    ).execute()
    assert result.published == 1
    assert calls == []
    assert len(ws_calls) == 1
    assert ws_calls[0]["user_ids"] == ["online-user"]


def test_publish_due_soon_toasts_online_and_portals_offline(monkeypatch) -> None:
    from commercial_app.application.services import (
        task_portal_notification_delivery_policy as policy_mod,
    )
    from commercial_app.application.services import commercial_realtime_notify as notify_mod

    class _Hub:
        def is_user_online(self, user_id: str | None) -> bool:
            return str(user_id or "") == "online-user"

    monkeypatch.setattr(policy_mod, "commercial_realtime_hub", _Hub())
    ws_calls: list[dict] = []

    def _capture_wl(**kwargs):
        ws_calls.append(kwargs)

    monkeypatch.setattr(notify_mod, "notify_worklist_changed", _capture_wl)
    outbox = _OutboxMemory()
    outbox.enqueue(
        event_type="commercial.task.due_soon",
        aggregate_type="commercial_task",
        aggregate_id="task-1",
        payload={
            "taskId": "task-1",
            "title": "Ligar ACME",
            "dueAt": "2026-08-18T12:00:00+00:00",
            "userIds": ["online-user", "offline-user"],
            "actionTarget": "/apps/commercial/my-tasks",
            "dedupeKey": "commercial:task:due_soon:task-1",
            "bucket": "today",
        },
    )
    portal_calls: list[dict] = []

    class _Notifier(CommercialPortalNotificationService):
        def __init__(self) -> None:
            super().__init__(enabled=True, service_token="tok")

        def notify_task_event(self, **kwargs):  # type: ignore[override]
            portal_calls.append(kwargs)
            return True

    result = PublishIntegrationOutboxUseCase(
        outbox=outbox,
        notifier=_Notifier(),
    ).execute()
    assert result.published == 1
    assert ws_calls[0]["reason"] == "task.due_soon"
    assert ws_calls[0]["assignee_user_ids"] == ["online-user"]
    assert portal_calls[0]["user_ids"] == ["offline-user"]


def test_portal_notification_payload_shape(monkeypatch) -> None:
    captured: dict = {}

    class _Resp:
        status_code = 200
        text = "ok"

    def _post(url, *, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr(
        "commercial_app.application.services.commercial_portal_notification_service.httpx.post",
        _post,
    )
    svc = CommercialPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="secret",
        enabled=True,
    )
    assert svc.notify_ready_to_invoice(
        user_ids=["u1"],
        permission_codes=["commercial.billing.notify"],
        line_key="01|1|01",
        pedido="1",
        linha="01",
        cliente="ACME",
        filial="01",
    )
    body = captured["json"]
    assert body["category"] == "commercial"
    assert body["sourceApp"] == "commercial"
    assert body["action"]["type"] == "portal_route"
    assert body["action"]["label"] == "Abrir pedidos"
    assert "stage=ready_to_invoice" in body["action"]["target"]
    assert "view=board" not in body["action"]["target"]
    assert "q=1" in body["action"]["target"]
    assert "branch=01" in body["action"]["target"]
    assert body["userIds"] == ["u1"]
    assert body["permissionCodes"] == ["commercial.billing.notify"]
    assert body["metadata"]["dedupeKey"] == "commercial:ready_to_invoice:01|1|01"
