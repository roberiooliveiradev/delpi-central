"""Chamado #1551: FIFO fiscal provisório sem baixa dupla da coleta WEG."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from production_control_app.domain.services.myweg_demand_projection import (
    project_myweg_demand_lines,
)
from production_control_app.domain.services.myweg_fiscal_fifo_offset import (
    reconcile_latest_myweg_fifo,
)

TODAY = date(2026, 11, 9)
BATCH = {
    "id": "batch-09",
    "collection_date": "2026-11-09",
    "collected_at": "2026-11-09T04:00:00-03:00",
}


def _projection(*quantities: tuple[str, str]) -> list:
    rows = []
    for idx, (due, qty) in enumerate(quantities):
        rows.append({
            "id": f"r{idx+1}",
            "line_no": idx + 1,
            "material_weg_tratado": "MAT-90263918",
            "codigo_referencia_weg": "90263918",
            "data_remessa": due,
            "quantidade_original_un": qty,
            "quantidade_mi": str(Decimal(qty) / Decimal("1000")),
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": "90263918",
                "matched_by": "code_and_reference",
            },
        })
    return project_myweg_demand_lines(
        rows, batch_id=BATCH["id"], collected_at=BATCH["collected_at"],
    )


def _nf(
    quantity: str,
    *,
    doc: str = "017071",
    item: str = "04",
    issue_date: str = "2026-11-09",
    customer: str = "000001",
    store: str = "09",
    comparable: bool = True,
) -> dict:
    return {
        "branch": "02",
        "customer_code": customer,
        "customer_store": store,
        "product_code": "90263918",
        "invoice_number": doc,
        "invoice_series": "02",
        "item": item,
        "issue_date": issue_date,
        "unit": "MI",
        "quantity": "0.006",
        "quantity_un": quantity,
        "comparable": comparable,
        "is_return": False,
        "situation": "emitted",
    }


def _apply(lines: list, invoices: list[dict], batch: dict | None = None) -> dict:
    return reconcile_latest_myweg_fifo(
        lines, invoices, batch=(BATCH if batch is None else batch), today=TODAY,
    )


def test_real_case_90263918_nf_017071_converts_six_pieces_to_zero() -> None:
    """SD2 0,006 MI = 6 UN, já normalizado em quantity_un pela api-delpi."""
    original = _projection(("2026-11-09", "6"))
    result = _apply(original, [_nf("6")])
    assert original[0].open_quantity == Decimal("6")
    assert result["lines"][0].open_quantity == Decimal("0")
    assert result["allocations"]["r1"]["applied_quantity_un"] == "6"
    assert result["meta"]["applied_un"] == "6"
    assert result["meta"]["status"] == "provisional"
    assert result["meta"]["recognition_status"] == "weg_acknowledgment_not_proven"
    assert result["pending_products"] == set()
    assert result["allocations"]["r1"]["invoices"][0]["fiscal_key"] == "02|017071|02|04"


def test_fifo_allocates_oldest_due_date_with_unequal_sales_order_quantity() -> None:
    """Não depende da quantidade original do pedido de venda: NF é autoridade."""
    original = _projection(
        ("2026-11-10", "4"),
        ("2026-11-12", "8"),
        ("2026-11-15", "3"),
    )
    result = _apply(original, [_nf("6")])
    assert [r.open_quantity for r in result["lines"]] == [
        Decimal("0"), Decimal("6"), Decimal("3"),
    ]
    assert result["allocations"]["r1"]["applied_quantity_un"] == "4"
    assert result["allocations"]["r2"]["applied_quantity_un"] == "2"
    assert "r3" not in result["allocations"]


def test_multiple_nf_items_and_repeat_read_are_idempotent() -> None:
    original = _projection(("2026-11-10", "11"))
    invoices = [
        _nf("6", doc="017071", item="04"),
        _nf("3", doc="017072", item="01"),
        _nf("6", doc="017071", item="04"),  # join duplicate
    ]
    result1 = _apply(original, invoices)
    result2 = _apply(original, invoices)
    assert result1["lines"][0].open_quantity == Decimal("2")
    assert result2["lines"][0].open_quantity == Decimal("2")
    assert result1["meta"]["applied_un"] == "9"
    assert result1["meta"]["applied_item_count"] == 2


def test_extra_fiscal_quantity_stays_unused_without_negative_need() -> None:
    result = _apply(_projection(("2026-11-10", "6")), [_nf("10")])
    assert result["lines"][0].open_quantity == Decimal("0")
    assert result["meta"]["products"][0]["unapplied_fiscal_un"] == "4"


def test_fiscal_product_from_another_customer_does_not_reduce_weg_need() -> None:
    result = _apply(_projection(("2026-11-10", "6")), [_nf("6", customer="000050")])
    assert result["lines"][0].open_quantity == Decimal("6")
    assert "90263918" in result["pending_products"]


def test_uncomparable_units_block_product_instead_of_partial_silent_credit() -> None:
    result = _apply(
        _projection(("2026-11-10", "6")),
        [_nf("5"), _nf("1", doc="017073", comparable=False)],
    )
    assert result["lines"][0].open_quantity == Decimal("6")
    assert result["meta"]["status"] == "partial"
    assert "90263918" in result["pending_products"]


def test_same_day_late_collection_cannot_prove_nf_after_snapshot() -> None:
    late_batch = {
        **BATCH,
        "collected_at": "2026-11-09T14:00:00-03:00",
    }
    result = _apply(
        _projection(("2026-11-10", "6")), [_nf("6")],
        batch=late_batch,
    )
    assert result["lines"][0].open_quantity == Decimal("6")
    assert result["pending_products"] == {"90263918"}


def test_next_snapshot_does_not_reapply_invoices_from_previous_date() -> None:
    later_batch = {
        "id": "batch-10",
        "collection_date": "2026-11-10",
        "collected_at": "2026-11-10T04:00:00-03:00",
    }
    result = reconcile_latest_myweg_fifo(
        _projection(("2026-11-12", "4")),
        [_nf("6", issue_date="2026-11-09")],
        batch=later_batch,
        today=date(2026, 11, 10),
    )
    assert result["lines"][0].open_quantity == Decimal("4")
    assert result["meta"]["applied_un"] == "0"


def test_invalid_snapshot_date_blocks_auto_reconciliation() -> None:
    result = _apply(_projection(("2026-11-10", "6")), [_nf("6")], batch={})
    assert result["meta"]["status"] == "snapshot_date_unverified"
    assert result["pending_products"] == {"90263918"}


def test_zero_and_mixed_quantity_not_silently_converted() -> None:
    result = _apply(_projection(("2026-11-10", "6")), [_nf("0.5")])
    assert result["pending_products"] == {"90263918"}
    assert result["lines"][0].open_quantity == Decimal("6")
