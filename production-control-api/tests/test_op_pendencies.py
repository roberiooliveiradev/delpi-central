"""Regressões #1548: recomendação D-2, agrupamento e cobertura confiável."""

from __future__ import annotations

from datetime import date

from production_control_app.domain.services.demand_coverage_service import DemandLine
from production_control_app.domain.services.op_pendency_service import build_op_pendencies

TODAY = date(2026, 11, 9)


def _line(
    product: str = "90263964",
    *,
    due: date | None = date(2026, 11, 20),
    uncovered: float = 0.25,
    source: str = "myweg",
    unit: str = "MI",
    order: str = "MYWEG",
    line_item: str = "01",
    incomplete: bool = False,
) -> DemandLine:
    return DemandLine(
        branch="02",
        sales_order=order,
        line_item=line_item,
        customer_name="WEG Linhares" if source == "myweg" else "Cliente ERP",
        customer_code="000001",
        customer_store="09",
        customer_order="PO-01",
        order_type="N",
        product_code=product,
        ordered_quantity=uncovered,
        delivered_quantity=0,
        open_quantity=uncovered,
        due_date=due,
        dispatch_date=None,
        product_stock=0,
        unit=unit,
        uncovered_quantity=uncovered,
        source=source,
    )


def test_due_minus_two_calendar_days_and_grouped_pieces() -> None:
    early = _line(due=date(2026, 11, 20), uncovered=0.25, line_item="A")
    later = _line(
        due=date(2026, 11, 25), uncovered=0.15,
        source="protheus", order="P01", line_item="B",
    )
    payload = build_op_pendencies([early, later], branch="02", today=TODAY)
    assert payload["count"] == 1
    item = payload["items"][0]
    assert item["suggested_op_date"] == "2026-11-18"
    assert item["next_uncovered_pieces"] == 250
    assert item["total_uncovered_pieces"] == 400
    assert item["demand_count"] == 2
    assert item["origins"] == ["myweg", "protheus"]
    assert [x["suggested_op_date"] for x in item["schedule"]] == [
        "2026-11-18", "2026-11-23",
    ]


def test_overdue_today_and_tomorrow_are_suggested_for_today() -> None:
    lines = [
        _line("A", due=date(2026, 11, 5), uncovered=0.026),
        _line("B", due=date(2026, 11, 10), uncovered=0.2),
    ]
    payload = build_op_pendencies(lines, branch="02", today=TODAY)
    assert [item["suggested_op_date"] for item in payload["items"]] == [
        "2026-11-09", "2026-11-09"
    ]
    assert payload["items"][0]["next_uncovered_pieces"] == 26


def test_partially_covered_only_reports_real_shortfall() -> None:
    covered = _line("COVERED", uncovered=0)
    pending = _line("PARTIAL", uncovered=0.026)
    payload = build_op_pendencies([covered, pending], branch="02", today=TODAY)
    assert payload["count"] == 1
    assert payload["items"][0]["product_code"] == "PARTIAL"
    assert payload["items"][0]["next_uncovered_pieces"] == 26


def test_unverified_op_and_stock_product_are_not_reported_as_missing_op() -> None:
    line = _line("UNKNOWN", uncovered=0.9)
    line.op_coverage_incomplete = True
    payload = build_op_pendencies(
        [line, _line("STOCK-MISSING", uncovered=0.1)],
        branch="02",
        today=TODAY,
        incomplete_products={"STOCK-MISSING"},
    )
    assert payload["count"] == 0
    assert payload["suppressed_product_count"] == 2


def test_unit_conversion_is_safe_for_pc_and_unknown() -> None:
    payload = build_op_pendencies(
        [
            _line("PC-PRODUCT", uncovered=120, unit="PC"),
            _line("UNKNOWN-PRODUCT", uncovered=0.2, unit=""),
        ],
        branch="02",
        today=TODAY,
    )
    lookup = {x["product_code"]: x for x in payload["items"]}
    assert lookup["PC-PRODUCT"]["next_uncovered_pieces"] == 120
    assert lookup["UNKNOWN-PRODUCT"]["next_uncovered_pieces"] is None
    assert lookup["UNKNOWN-PRODUCT"]["unit"] == "UNSPECIFIED"


def test_different_branches_do_not_mix() -> None:
    line = _line()
    line.branch = "01"
    payload = build_op_pendencies([line], branch="02", today=TODAY)
    assert payload["count"] == 0


def test_missing_due_date_does_not_invent_a_deadline() -> None:
    payload = build_op_pendencies(
        [_line(due=None)], branch="02", today=TODAY
    )
    item = payload["items"][0]
    assert item["required_date"] is None
    assert item["suggested_op_date"] is None


def test_same_product_with_conflicting_units_is_withheld() -> None:
    payload = build_op_pendencies(
        [
            _line(unit="PC", line_item="01"),
            _line(unit="MI", line_item="02"),
        ],
        branch="02", today=TODAY,
    )
    assert payload["count"] == 0
    assert payload["suppressed_product_count"] == 1
