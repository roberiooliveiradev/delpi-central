"""Empilhamento DE0/RE0 das transferências entre armazéns."""

from production_control_app.domain.services.line_feeder_warehouse_transfers import (
    pair_warehouse_transfers,
)


def _row(**overrides):
    item = {
        "cf": "DE0",
        "document": "000123",
        "location": "01",
        "quantity": 4.0,
        "issue_date": "2026-09-20",
        "product_code": "50320064",
        "user_name": "JOAO",
    }
    item.update(overrides)
    return item


def test_pair_joins_de0_and_re0_of_same_document() -> None:
    items = pair_warehouse_transfers(
        [
            _row(cf="DE0", location="01", quantity=4.0),
            _row(cf="RE0", location="99", quantity=4.0),
        ]
    )
    assert len(items) == 1
    assert items[0]["from_warehouse"] == "01"
    assert items[0]["to_warehouse"] == "99"
    assert items[0]["quantity"] == 4.0
    assert items[0]["document"] == "000123"


def test_pair_keeps_orphan_side_empty() -> None:
    items = pair_warehouse_transfers([_row(cf="DE0", location="01")])
    assert items[0]["from_warehouse"] == "01"
    assert items[0]["to_warehouse"] == ""


def test_pair_ignores_production_and_consumption_cf() -> None:
    items = pair_warehouse_transfers(
        [
            _row(cf="PR0", document="P1", location="01"),
            _row(cf="999", document="C1", location="99"),
            _row(cf="DE0", document="T1", location="01"),
            _row(cf="RE0", document="T1", location="99"),
        ]
    )
    assert [row["document"] for row in items] == ["T1"]
