"""Testes do agrupamento de pedidos de compra (SC7)."""

from __future__ import annotations

from app.domain.services.lancamento_notas_fiscais.purchase_order_grouping_service import (
    find_purchase_order_group,
    format_linked_po_label,
    format_linked_po_labels,
    group_open_purchase_order_lines,
    linked_po_snapshot_from_request,
    linked_po_snapshots_from_request,
)


def test_group_splits_same_pc_by_delivery_date() -> None:
    groups = group_open_purchase_order_lines(
        [
            {
                "order_number": "000123",
                "product_code": "A",
                "open_value": 10,
                "issue_date": "2026-07-02",
                "expected_delivery_date": "2026-07-20",
            },
            {
                "order_number": "000123",
                "product_code": "B",
                "open_value": 20,
                "issue_date": "2026-07-01",
                "expected_delivery_date": "2026-07-20",
            },
            {
                "order_number": "000123",
                "product_code": "A",
                "open_value": 5,
                "issue_date": "2026-07-03",
                "expected_delivery_date": "2026-07-25",
            },
            {
                "order_number": "000123",
                "product_code": "C",
                "open_value": 7,
                "issue_date": None,
                "expected_delivery_date": None,
            },
        ]
    )
    assert len(groups) == 3
    by_delivery = {g["delivery_date"]: g for g in groups}
    assert by_delivery["2026-07-20"]["product_count"] == 2
    assert by_delivery["2026-07-20"]["open_value"] == 30.0
    assert by_delivery["2026-07-20"]["issue_date"] == "2026-07-01"
    assert by_delivery["2026-07-25"]["product_count"] == 1
    assert by_delivery[None]["product_count"] == 1
    assert by_delivery[None]["open_value"] == 7.0


def test_find_group_and_snapshot_helpers() -> None:
    groups = group_open_purchase_order_lines(
        [
            {
                "order_number": "0001",
                "product_code": "X",
                "open_value": 1,
                "expected_delivery_date": "",
            }
        ]
    )
    found = find_purchase_order_group(
        groups, order_number="0001", delivery_date=None
    )
    assert found is not None
    assert find_purchase_order_group(
        groups, order_number="0001", delivery_date="2026-01-01"
    ) is None
    assert linked_po_snapshot_from_request({}) is None
    assert linked_po_snapshot_from_request({"linked_po_number": "0001"})[
        "order_number"
    ] == "0001"
    assert format_linked_po_label(
        order_number="000123", delivery_date="2026-07-20"
    ) == "PC 000123 · entrega 20/07/2026"
    assert "sem data" in format_linked_po_label(
        order_number="000123", delivery_date=None
    )
    assert linked_po_snapshots_from_request(
        {
            "linked_purchase_orders": [
                {"order_number": "A", "delivery_date": None},
                {"order_number": "B", "delivery_date": "2026-07-01"},
            ]
        }
    ) == [
        {
            "order_number": "A",
            "delivery_date": None,
            "issue_date": None,
            "open_value": None,
            "product_count": None,
            "linked_at": None,
            "linked_by_user_id": None,
            "linked_by_name": None,
        },
        {
            "order_number": "B",
            "delivery_date": "2026-07-01",
            "issue_date": None,
            "open_value": None,
            "product_count": None,
            "linked_at": None,
            "linked_by_user_id": None,
            "linked_by_name": None,
        },
    ]
    assert format_linked_po_labels(
        [{"order_number": "A", "delivery_date": None}]
    ).startswith("PC A")
