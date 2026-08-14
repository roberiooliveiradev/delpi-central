"""Conferência derivada dos dados coletados."""

from app.domain.services.invoice_issuance.review_checklist import build_review_checklist


def test_review_checklist_marks_completed_fields() -> None:
    flags = build_review_checklist(
        party_code="000001",
        party_store="01",
        items=[
            {
                "product_code": "90260001",
                "quantity": "1",
                "unit_price": "10,00",
                "stock_write_off": False,
            }
        ],
        invoice_type="sale",
        invoice_type_other=None,
        freight_mode="cif",
        weight_kg="1.5",
        volume_count=2,
    )
    assert all(flags.values())
    assert "purchase_order" not in flags


def test_review_checklist_incomplete_without_party() -> None:
    flags = build_review_checklist(
        party_code="",
        party_store="",
        items=[],
        invoice_type="other",
        invoice_type_other="",
        freight_mode="cif",
        weight_kg=None,
        volume_count=0,
    )
    assert flags["recipient"] is False
    assert flags["item_codes"] is False
    assert flags["invoice_type"] is False
    assert flags["weight_volumes"] is False
