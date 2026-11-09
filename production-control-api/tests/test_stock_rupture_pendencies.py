"""Chamado #1549: rupturas oficiais no card Pendências do Portal PCP."""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from production_control_app.application.services.demand_service import (
    DemandService,
    _StockRuptureSnapshotCache,
)
from production_control_app.domain.services.demand_coverage_service import DemandLine
from production_control_app.domain.services.stock_rupture_pendency_service import (
    build_stock_rupture_pendencies,
    merge_pendency_items,
)

TODAY = date(2026, 11, 9)


def _rupture(code: str, date_iso: str, *, branch: str = "02", unit: str = "MT") -> dict:
    return {
        "product_code": code,
        "product_description": "Cabo de cobre",
        "branch": branch,
        "unit": unit,
        "first_shortage_date": date_iso,
        "available_stock": 30.5,
        "shortage_balance": -12.25,
        "next_purchase": "PC 000123 - previsão 2026-11-13",
        "observation": "Priorizar o recebimento",
        "last_inventory_date": None,
    }


def _line() -> DemandLine:
    return DemandLine(
        branch="02", sales_order="P1", line_item="01",
        customer_name="WEG", customer_code="000001", customer_store="09",
        customer_order="PO-01", order_type="N", product_code="90263964",
        ordered_quantity=0.026, delivered_quantity=0, open_quantity=0.026,
        due_date=date(2026, 11, 10), dispatch_date=None,
        product_stock=0, unit="MI", uncovered_quantity=0.026,
        source="protheus",
    )


class _Gateway:
    def __init__(self, rows: list[dict], *, fails: bool = False) -> None:
        self.rows = rows
        self.calls = 0
        self.fails = fails

    def fetch_stock_rupture_pendencies(self, *, branch: str, horizon_days: int = 30) -> dict:
        self.calls += 1
        assert branch == "02"
        assert horizon_days == 30
        if self.fails:
            raise RuntimeError("Delpi Reports temporariamente indisponível")
        return {"data": {
            "items": self.rows, "meta": {"branch": branch, "asOfDate": TODAY.isoformat()}
        }}


def _service(gateway: _Gateway, *, ttl: int = 0) -> DemandService:
    service = DemandService(
        gateway, today=TODAY, stock_rupture_cache=_StockRuptureSnapshotCache(ttl)
    )
    service._load_origin_lines = lambda user, *, branch, origin, refresh=False: (
        [_line()], None
    )
    return service


def _user() -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=True, permissions=set())


def test_stock_rupture_keeps_unit_and_canonical_projection_fields() -> None:
    items = build_stock_rupture_pendencies(
        [_rupture("10080001", "2026-11-10", unit="KG")],
        branch="02", today=TODAY,
    )
    assert len(items) == 1
    assert items[0]["kind"] == "stock_rupture"
    assert items[0]["shortage_balance"] == -12.25
    assert items[0]["available_stock"] == 30.5
    assert items[0]["unit"] == "KG"
    assert items[0]["next_purchase"].startswith("PC 000123")
    assert items[0]["provider_key"] == "safety_stock_shortage_30d"


def test_ruptures_include_overdue_and_limit_to_next_30_days() -> None:
    items = build_stock_rupture_pendencies(
        [
            _rupture("LATE", "2026-10-01"),
            _rupture("TODAY", "2026-11-09"),
            _rupture("END", "2026-12-09"),
            _rupture("TOO-LATE", "2026-12-10"),
            _rupture("OTHER-BRANCH", "2026-11-10", branch="01"),
            _rupture("INVALID", "sem-data"),
        ],
        branch="02", today=TODAY,
    )
    assert [i["product_code"] for i in items] == ["LATE", "TODAY", "END"]


def test_dedup_same_material_keeps_earliest_shortage() -> None:
    result = build_stock_rupture_pendencies(
        [_rupture("MP-A", "2026-11-15"), _rupture("MP-A", "2026-11-12")],
        branch="02", today=TODAY,
    )
    assert len(result) == 1
    assert result[0]["first_shortage_date"] == "2026-11-12"


def test_merge_interleaves_op_date_and_rupture_date_with_stable_tie() -> None:
    ops = [
        {
            "id": "02|include-production-order|X",
            "kind": "include_production_order",
            "suggested_op_date": "2026-11-09",
            "product_code": "X",
        },
        {
            "id": "02|include-production-order|Z",
            "kind": "include_production_order",
            "suggested_op_date": "2026-11-20",
            "product_code": "Z",
        },
    ]
    ruptures = build_stock_rupture_pendencies(
        [
            _rupture("MP-C", "2026-11-08"),
            _rupture("MP-A", "2026-11-09"),
            _rupture("MP-B", "2026-11-18"),
        ],
        branch="02", today=TODAY,
    )
    merged = merge_pendency_items(ops, ruptures)
    assert [r["product_code"] for r in merged] == ["MP-C", "MP-A", "X", "MP-B", "Z"]


def test_combined_bff_counts_and_preserves_op_pendencies() -> None:
    gateway = _Gateway([_rupture("10080001", "2026-11-09")])
    payload = _service(gateway).list_op_pendencies(_user(), branch="02")
    assert payload["count"] == 2
    assert payload["op_count"] == 1
    assert payload["stock_rupture_count"] == 1
    assert [item["kind"] for item in payload["items"]] == [
        "stock_rupture", "include_production_order",
    ]
    assert payload["stock_source_status"] == "complete"
    assert payload["source_status"] == "complete"
    assert payload["total_uncovered_pieces"] == 26


def test_reports_failure_keeps_ops_and_explicit_warning() -> None:
    gateway = _Gateway([], fails=True)
    payload = _service(gateway).list_op_pendencies(_user(), branch="02")
    assert payload["count"] == 1
    assert payload["op_count"] == 1
    assert payload["stock_rupture_count"] == 0
    assert payload["stock_source_status"] == "unavailable"
    assert payload["source_status"] == "partial"
    assert "Rupturas de estoque indisponíveis" in payload["warning"]


def test_stock_cache_ttl_is_used_and_refresh_bypasses_it() -> None:
    gateway = _Gateway([_rupture("MP-A", "2026-11-10")])
    service = _service(gateway, ttl=120)
    service.list_op_pendencies(_user(), branch="02")
    service.list_op_pendencies(_user(), branch="02")
    assert gateway.calls == 1
    service.list_op_pendencies(_user(), branch="02", refresh=True)
    assert gateway.calls == 2


def test_cross_branch_data_not_exposed_even_on_authorized_bff() -> None:
    gateway = _Gateway([
        _rupture("MP-CORRETO", "2026-11-09"),
        _rupture("MP-OUTRA-FILIAL", "2026-11-09", branch="01"),
    ])
    payload = _service(gateway).list_op_pendencies(_user(), branch="02")
    codes = {item["product_code"] for item in payload["items"]}
    assert "MP-CORRETO" in codes
    assert "MP-OUTRA-FILIAL" not in codes
