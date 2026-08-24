from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.delivery_map_service import DeliveryMapService
from production_control_app.application.services.public_delivery_map_access_service import (
    PublicDeliveryMapAccessService,
)
from production_control_app.domain.errors import SnapshotNotFound
from production_control_app.domain.services.conjunto_operation_progress import (
    compute_conjunto_progress,
    filter_operations_for_conjuntos,
)
from production_control_app.domain.services.delivery_map_grouping import group_delivery_map_sections
from production_control_app.domain.services.delivery_map_merge import (
    apply_override_updates,
    merge_overrides_after_refresh,
)
from production_control_app.domain.services.delivery_map_pull import normalize_pcp_order_row

FULL_PERMS = (
    "production-control.access",
    "production-control.delivery-map.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _user(*permissions: str, superadmin: bool = False):
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


def _pcp_item(**overrides: Any) -> dict[str, Any]:
    row = {
        "production_order": "10737601001",
        "product_code": "90262910",
        "product_description": "Produto teste",
        "due_date": "2026-08-20",
        "planned_qty": 6.0,
        "produced_qty": 0.0,
        "pending_qty": 6.0,
        "observation": "Observação",
        "days_late": 4,
        "is_delayed": True,
    }
    row.update(overrides)
    return row


def test_normalize_filters_non_pa_and_zero_balance() -> None:
    assert normalize_pcp_order_row(_pcp_item()) is not None
    assert normalize_pcp_order_row(_pcp_item(product_code="50120001")) is None
    assert normalize_pcp_order_row(_pcp_item(pending_qty=0)) is None


def test_grouping_puts_overdue_and_today_in_first_section() -> None:
    today = date(2026, 8, 24)
    orders = [
        {
            "production_order": "OP-LATE",
            "product_code": "90262910",
            "due_date": "2026-08-20",
            "planned_qty": 1,
            "produced_qty": 0,
            "pending_qty": 1,
            "observation": None,
            "days_late": 4,
            "is_delayed": True,
        },
        {
            "production_order": "OP-TODAY",
            "product_code": "90262911",
            "due_date": "2026-08-24",
            "planned_qty": 2,
            "produced_qty": 0,
            "pending_qty": 2,
            "observation": None,
            "days_late": 0,
            "is_delayed": False,
        },
        {
            "production_order": "OP-FUTURE",
            "product_code": "90262912",
            "due_date": "2026-08-26",
            "planned_qty": 3,
            "produced_qty": 0,
            "pending_qty": 3,
            "observation": None,
            "days_late": 0,
            "is_delayed": False,
        },
    ]
    sections = group_delivery_map_sections(orders, {}, today=today)
    assert sections[0]["section_key"] == "overdue_and_today"
    assert sections[0]["row_count"] == 2
    assert sections[1]["section_key"] == "2026-08-26"
    assert sections[1]["row_count"] == 1


def test_merge_overrides_keeps_only_existing_orders() -> None:
    merged = merge_overrides_after_refresh(
        previous_overrides={
            "OP-1": {"mp_ok": True, "work_center": "CDRL"},
            "OP-GONE": {"mp_ok": True, "work_center": "X"},
        },
        order_keys={"OP-1", "OP-2"},
    )
    assert merged == {"OP-1": {"mp_ok": True, "work_center": "CDRL"}}


def test_apply_override_updates() -> None:
    result = apply_override_updates(
        {},
        [{"production_order": "OP-1", "mp_ok": True, "work_center": "8"}],
    )
    assert result["OP-1"] == {"mp_ok": True, "work_center": "8"}


class _FakeSnapshots:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self._rows.get(branch)

    def upsert(
        self,
        *,
        branch: str,
        horizon_end: date,
        payload: dict[str, Any],
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        row = {
            "branch": branch,
            "horizon_end": horizon_end,
            "payload_json": payload,
            "refreshed_at": "2026-08-24T10:00:00+00:00",
            "refreshed_by": refreshed_by,
        }
        self._rows[branch] = row
        return row

    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._rows.get(branch)
        if row is None:
            raise RuntimeError("missing")
        row = {**row, "payload_json": payload}
        self._rows[branch] = row
        return row


class _FakeGateway:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self._items = items

    def fetch_pcp_orders_items_page(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "data": {
                "items": self._items,
                "pagination": {"is_complete": True, "total_pages": 1},
            }
        }


def test_service_seeds_and_groups() -> None:
    service = DeliveryMapService(
        _FakeGateway([_pcp_item(), _pcp_item(production_order="10888801001", due_date="2026-09-01")]),
        _FakeSnapshots(),
    )
    payload = service.build(_user(*FULL_PERMS), branch="01")
    assert payload["summary"]["order_count"] == 2
    assert payload["snapshot"]["seeded"] is True
    assert payload["sections"]


def test_service_refresh_preserves_overrides() -> None:
    snapshots = _FakeSnapshots()
    gateway = _FakeGateway([_pcp_item()])
    service = DeliveryMapService(gateway, snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    service.patch_overrides(
        _user(*FULL_PERMS),
        branch="01",
        updates=[{"production_order": "10737601001", "mp_ok": True, "work_center": "CDRL"}],
    )
    payload = service.refresh(_user(*FULL_PERMS), branch="01")
    row = payload["sections"][0]["rows"][0]
    assert row["mp_ok"] is True
    assert row["work_center"] == "CDRL"


def test_patch_requires_snapshot() -> None:
    service = DeliveryMapService(_FakeGateway([]), _FakeSnapshots())
    with pytest.raises(SnapshotNotFound):
        service.patch_overrides(
            _user(*FULL_PERMS),
            branch="01",
            updates=[{"production_order": "10737601001", "mp_ok": True}],
        )


def test_grouping_does_not_mark_partial_production_as_reported() -> None:
    today = date(2026, 8, 24)
    orders = [
        {
            "production_order": "OP-1",
            "product_code": "90262910",
            "due_date": "2026-08-24",
            "planned_qty": 10,
            "produced_qty": 5,
            "pending_qty": 5,
            "observation": "apontada",
            "days_late": 0,
            "is_delayed": False,
        }
    ]
    sections = group_delivery_map_sections(orders, {}, today=today)
    assert sections[0]["rows"][0]["is_reported"] is False


def test_conjunto_progress_weights_started_and_in_progress() -> None:
    stats = compute_conjunto_progress(
        [
            {"production_order": "10840401001", "operation_code": "01", "production_status": "started"},
            {"production_order": "10840401001", "operation_code": "02", "production_status": "in_progress", "is_in_production": True},
            {"production_order": "10840401001", "operation_code": "03", "production_status": "not_started"},
            {"production_order": "10840401001", "operation_code": "04", "production_status": "not_started"},
        ]
    )
    assert stats["total"] == 4
    assert stats["completed"] == 1
    assert stats["in_progress"] == 1
    assert stats["percent"] == 38


def test_public_delivery_map_token_matches_catalog_slug() -> None:
    access = PublicDeliveryMapAccessService()

    assert access.is_valid_token(access.token()) is True
    assert access.is_valid_token(" ABERTO ") is True
    assert access.is_valid_token("outro-token") is False


def test_build_public_requires_published_snapshot() -> None:
    service = DeliveryMapService(_FakeGateway([]), _FakeSnapshots())
    with pytest.raises(SnapshotNotFound):
        service.build_public(branch="01")


def test_build_public_strips_refreshed_by() -> None:
    snapshots = _FakeSnapshots()
    snapshots.upsert(
        branch="01",
        horizon_end=date(2026, 9, 30),
        payload={"orders": [_pcp_item()], "overrides": {}},
        refreshed_by="pcp.user",
    )
    service = DeliveryMapService(_FakeGateway([]), snapshots)
    payload = service.build_public(branch="01")
    assert payload["summary"]["order_count"] == 1
    assert "refreshed_by" not in payload["snapshot"]


def test_conjunto_progress_includes_intermediary_production_orders() -> None:
    operations = [
        {"production_order": "10840401001", "operation_code": "10", "production_status": "started"},
        {"production_order": "10840402001", "operation_code": "05", "production_status": "not_started"},
        {"production_order": "10840402001", "operation_code": "06", "production_status": "not_started"},
        {"production_order": "10840501001", "operation_code": "01", "production_status": "started"},
    ]
    grouped = filter_operations_for_conjuntos(operations, {"108404"})
    stats = compute_conjunto_progress(grouped["108404"])

    assert len(grouped["108404"]) == 3
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["percent"] == 33
