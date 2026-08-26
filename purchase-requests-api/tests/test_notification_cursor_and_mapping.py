from __future__ import annotations

from types import SimpleNamespace

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.use_cases.dispatch_purchase_order_linked_notifications_use_case import (
    DispatchPurchaseOrderLinkedNotificationsUseCase,
)


class _FakeMappingRepo:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = list(rows or [])

    def get_mapping_by_protheus_user_id(self, protheus_user_id: str) -> dict | None:
        normalized = (protheus_user_id or "").strip()
        matches = [
            row
            for row in self.rows
            if (row.get("protheus_user_id") or "").strip() == normalized
            and row.get("mapping_status") == "mapped"
        ]
        return dict(matches[0]) if matches else None

    def list_mappings(self) -> list[dict]:
        return list(self.rows)


class _FakeCursorRepo:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def get_last_recno(self, job_key: str) -> int | None:
        return self.values.get(job_key)

    def upsert_last_recno(self, job_key: str, last_recno: int) -> dict:
        self.values[job_key] = int(last_recno)
        return {"job_key": job_key, "last_recno": int(last_recno)}


class _FakeDispatchedRepo:
    def __init__(self) -> None:
        self.keys: set[tuple[str, str, str]] = set()

    def exists(self, *, branch: str, order_number: str, order_item: str) -> bool:
        return (branch, order_number, order_item) in self.keys

    def mark_dispatched(self, **kwargs) -> bool:
        key = (kwargs["branch"], kwargs["order_number"], kwargs["order_item"])
        if key in self.keys:
            return False
        self.keys.add(key)
        return True


class _FakeGateway:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def list_recent_linked_orders(self, *, after_recno: int = 0, limit: int = 100) -> dict:
        self.calls.append({"after_recno": after_recno, "limit": limit})
        return self.payload


class _FakeNotifier:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def notify_purchase_order_linked(self, **kwargs) -> bool:
        self.calls.append(kwargs)
        return True


def test_mapped_requester_resolves_zero_or_one_user() -> None:
    repo = _FakeMappingRepo(
        [
            {
                "user_id": "portal-1",
                "protheus_user_id": "000234",
                "mapping_status": "mapped",
            }
        ]
    )
    service = PurchaseRequestNotificationPreferenceService(
        mapping_repository=repo,
        subscription_repository=SimpleNamespace(),
    )
    assert service.portal_users_for_mapped_requester("000234") == ["portal-1"]
    assert service.portal_users_for_mapped_requester("missing") == []
    assert service.portal_users_for_mapped_requester("  ") == []


def test_first_run_only_persists_watermark() -> None:
    cursor = _FakeCursorRepo()
    notifier = _FakeNotifier()
    gateway = _FakeGateway(
        {
            "items": [
                {
                    "recno": 10,
                    "branch": "01",
                    "order_number": "041446",
                    "order_item": "0001",
                    "request_number": "164708",
                    "requester_protheus_user_id": "000234",
                    "product_code": "90XXXX",
                    "product_description": "CONECTOR",
                    "supplier_name": "ACME",
                    "expected_delivery_date": "2026-09-12",
                }
            ],
            "max_recno": 88,
        }
    )
    result = DispatchPurchaseOrderLinkedNotificationsUseCase(
        gateway=gateway,
        cursor_repository=cursor,
        dispatched_repository=_FakeDispatchedRepo(),
        preference_service=PurchaseRequestNotificationPreferenceService(
            mapping_repository=_FakeMappingRepo(
                [
                    {
                        "user_id": "portal-1",
                        "protheus_user_id": "000234",
                        "mapping_status": "mapped",
                    }
                ]
            )
        ),
        notification_service=notifier,
        job_key="purchase_order_linked",
    ).execute()

    assert result["first_run"] is True
    assert result["dispatched"] == 0
    assert result["last_recno"] == 88
    assert cursor.values["purchase_order_linked"] == 88
    assert notifier.calls == []
