from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.rnc_8d_quantity_field_service import (
    format_quantity_and_unit,
    normalize_template_payload_quantity_fields,
    resolve_quantity_display,
    split_quantity_and_unit,
)


def test_split_quantity_and_unit_from_legacy_string():
    qty, unit = split_quantity_and_unit("05 UNIDADES")
    assert qty == 5
    assert unit == "UNIDADES"


def test_normalize_template_payload_splits_legacy_combined_fields():
    payload = normalize_template_payload_quantity_fields(
        {
            "defective_quantity": "05 UNIDADES",
            "batch_quantity": "10 PC",
            "rejected_quantity": 3,
            "rejected_quantity_unit": "PEÇAS",
        }
    )
    assert payload["defective_quantity"] == 5
    assert payload["defective_quantity_unit"] == "UNIDADES"
    assert payload["batch_quantity"] == 10
    assert payload["batch_quantity_unit"] == "PC"
    assert payload["rejected_quantity"] == 3
    assert payload["rejected_quantity_unit"] == "PEÇAS"


def test_resolve_quantity_display_prefers_split_fields():
    display = resolve_quantity_display(
        {"defective_quantity": 5, "defective_quantity_unit": "UNIDADES"},
        "defective_quantity",
        "defective_quantity_unit",
    )
    assert display == "5 UNIDADES"


def test_format_quantity_and_unit_falls_back_to_legacy():
    assert format_quantity_and_unit(None, None, legacy_combined="05 UNIDADES") == "05 UNIDADES"
