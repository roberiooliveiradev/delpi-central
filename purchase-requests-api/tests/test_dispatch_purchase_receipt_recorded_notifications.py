from __future__ import annotations

from types import SimpleNamespace

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.application.use_cases.dispatch_purchase_receipt_recorded_notifications_use_case import (
    DispatchPurchaseReceiptRecordedNotificationsUseCase,
)
from purchase_requests_app.domain.services.purchase_receipt_recorded_notification_content_service import (
    PurchaseReceiptRecordedNotificationContentService,
)


class _FakeMappingRepo:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = list(rows or [])

    def get_mapping_by_protheus_user_id(self, protheus_user_id: str) -> dict | None:
        normalized = (protheus_user_id or "").strip()
        for row in self.rows:
            if (
                (row.get("protheus_user_id") or "").strip() == normalized
                and row.get("mapping_status") == "mapped"
            ):
                return dict(row)
        return None


class _FakeCursorRepo:
    def __init__(self, initial: int | None = None) -> None:
        self.values: dict[str, int] = {}
        if initial is not None:
            self.values["purchase_receipt_recorded"] = initial

    def get_last_recno(self, job_key: str) -> int | None:
        return self.values.get(job_key)

    def upsert_last_recno(self, job_key: str, last_recno: int) -> dict:
        self.values[job_key] = int(last_recno)
        return {"job_key": job_key, "last_recno": int(last_recno)}


class _FakeDispatchedRepo:
    def __init__(self) -> None:
        self.keys: set[tuple[str, str, str, str]] = set()

    def exists(
        self,
        *,
        branch: str,
        invoice_number: str,
        invoice_series: str,
        invoice_item: str,
    ) -> bool:
        return (branch, invoice_number, invoice_series, invoice_item) in self.keys

    def mark_dispatched(self, **kwargs) -> bool:
        key = (
            kwargs["branch"],
            kwargs["invoice_number"],
            kwargs["invoice_series"],
            kwargs["invoice_item"],
        )
        if key in self.keys:
            return False
        self.keys.add(key)
        return True


class _FakeGateway:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def list_recent_linked_receipts(self, *, after_recno: int = 0, limit: int = 100) -> dict:
        return self.payload


def _receipt_item(**overrides) -> dict:
    item = {
        "recno": 501,
        "branch": "01",
        "invoice_number": "000123456",
        "invoice_series": "1",
        "invoice_item": "0001",
        "order_number": "041446",
        "order_item": "0001",
        "request_number": "164708",
        "requester_protheus_user_id": "000234",
        "product_code": "90XXXX",
        "product_description": "CONECTOR",
        "supplier_name": "ACME",
        "quantity": 12.0,
        "entry_date": "2026-08-27",
    }
    item.update(overrides)
    return item


def _use_case(
    *,
    gateway: _FakeGateway,
    cursor: _FakeCursorRepo,
    dispatched: _FakeDispatchedRepo,
    notifier,
    mapped: bool = True,
) -> DispatchPurchaseReceiptRecordedNotificationsUseCase:
    rows = (
        [
            {
                "user_id": "portal-1",
                "protheus_user_id": "000234",
                "mapping_status": "mapped",
            }
        ]
        if mapped
        else []
    )
    return DispatchPurchaseReceiptRecordedNotificationsUseCase(
        gateway=gateway,
        cursor_repository=cursor,
        dispatched_repository=dispatched,
        preference_service=PurchaseRequestNotificationPreferenceService(
            mapping_repository=_FakeMappingRepo(rows),
            subscription_repository=SimpleNamespace(),
        ),
        notification_service=notifier,
    )


def test_first_run_does_not_post_to_core() -> None:
    posts: list[dict] = []

    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=201, text="")

    notifier = PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_receipt_item()], "max_recno": 900}),
        cursor=_FakeCursorRepo(initial=None),
        dispatched=_FakeDispatchedRepo(),
        notifier=notifier,
    ).execute()
    assert result["first_run"] is True
    assert result["dispatched"] == 0
    assert posts == []


def test_second_run_with_mapping_dispatches_once() -> None:
    posts: list[dict] = []

    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=201, text="")

    notifier = PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )
    cursor = _FakeCursorRepo(initial=500)
    dispatched = _FakeDispatchedRepo()
    use_case = _use_case(
        gateway=_FakeGateway({"items": [_receipt_item(recno=501)], "max_recno": 501}),
        cursor=cursor,
        dispatched=dispatched,
        notifier=notifier,
    )
    first = use_case.execute()
    assert first["first_run"] is False
    assert first["dispatched"] == 1
    assert len(posts) == 1
    body = posts[0]["json"]
    assert body["userIds"] == ["portal-1"]
    assert "permissionCodes" not in body
    assert body["metadata"]["event"] == "purchase_receipt_recorded"
    assert body["metadata"]["dedupeKey"] == (
        "purchase-requests:purchase_receipt_recorded:01:000123456:1:0001"
    )
    assert body["action"]["target"] == (
        "/apps/purchase-requests?branch=01&request_number=164708"
    )
    assert "164708" in body["title"]
    assert "000123456" in body["title"]
    assert "90XXXX" in body["message"]
    assert "CONECTOR" in body["message"]
    assert "ACME" in body["message"]
    assert "12" in body["message"]
    assert "27/08/2026" in body["message"]
    assert cursor.values["purchase_receipt_recorded"] == 501

    replay = use_case.execute()
    assert replay["dispatched"] == 0
    assert len(posts) == 1


def test_unmapped_requester_skips_without_post() -> None:
    posts: list[dict] = []

    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=201, text="")

    notifier = PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )
    result = _use_case(
        gateway=_FakeGateway({"items": [_receipt_item()], "max_recno": 501}),
        cursor=_FakeCursorRepo(initial=500),
        dispatched=_FakeDispatchedRepo(),
        notifier=notifier,
        mapped=False,
    ).execute()
    assert result["dispatched"] == 0
    assert posts == []


def test_core_no_app_access_skips_and_advances_cursor() -> None:
    posts: list[dict] = []

    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(
            status_code=400,
            text=(
                '{"errors":[{"code":"validation_error",'
                '"message":"no recipients have access to the source application '
                '(assign app permission in Minha DELPI RBAC)","path":"_global"}]}'
            ),
        )

    notifier = PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )
    cursor = _FakeCursorRepo(initial=500)
    result = _use_case(
        gateway=_FakeGateway(
            {
                "items": [
                    _receipt_item(recno=501),
                    _receipt_item(recno=502, invoice_number="000123457", invoice_item="0002"),
                ],
                "max_recno": 502,
            }
        ),
        cursor=cursor,
        dispatched=_FakeDispatchedRepo(),
        notifier=notifier,
    ).execute()
    assert result["dispatched"] == 0
    assert result["skipped"] == 2
    assert cursor.values["purchase_receipt_recorded"] == 502
    assert len(posts) == 2


def test_core_server_error_stops_cursor() -> None:
    posts: list[dict] = []

    def fake_post(url, **kwargs):
        posts.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=503, text="unavailable")

    notifier = PurchaseRequestsPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="token",
        enabled=True,
        http_post=fake_post,
    )
    cursor = _FakeCursorRepo(initial=500)
    result = _use_case(
        gateway=_FakeGateway(
            {
                "items": [
                    _receipt_item(recno=501),
                    _receipt_item(recno=502, invoice_number="000123457"),
                ],
                "max_recno": 502,
            }
        ),
        cursor=cursor,
        dispatched=_FakeDispatchedRepo(),
        notifier=notifier,
    ).execute()
    assert result["dispatched"] == 0
    assert result["skipped"] == 1
    assert cursor.values["purchase_receipt_recorded"] == 500
    assert len(posts) == 1


def test_content_title_message_and_deep_link() -> None:
    content = PurchaseReceiptRecordedNotificationContentService
    assert content.format_title(request_number="164708", invoice_number="000123456") == (
        "Recebimento da SC 164708 — NF 000123456"
    )
    assert content.build_deep_link_path(branch="02", request_number="164708") == (
        "/apps/purchase-requests?branch=02&request_number=164708"
    )
    message = content.format_message(
        product_code="90XXXX",
        product_description="CONECTOR",
        supplier_name="ACME",
        quantity=12,
        entry_date="20260827",
    )
    assert "90XXXX" in message
    assert "12" in message
    assert "27/08/2026" in message
