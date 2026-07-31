"""Regressão — aliases canônicos não quebram lookup OP→produto (quality-labels)."""

from __future__ import annotations

from app.domain.services.production.production_order_item_alias_service import (
    ProductionOrderItemAliasService,
)


def test_quality_labels_consumes_product_description_after_alias() -> None:
    """quality-labels lê product_description; listagens SC2 passam a espelhar o campo."""
    row = ProductionOrderItemAliasService.enrich_list_item(
        {
            "production_order": "24689101001",
            "branch": "01",
            "product_code": "90300005",
            "description": "RESISTOR",
            "order_number": "246891",
        }
    )
    assert row is not None
    assert row["product_description"] == "RESISTOR"
    # Mesmo contrato usado em quality_labels_service.resolve
    assert str(row.get("product_code") or "").strip() == "90300005"
    assert str(row.get("product_description") or "").strip() == "RESISTOR"
