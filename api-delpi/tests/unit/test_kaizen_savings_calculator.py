from __future__ import annotations

import pytest

from app.domain.services.kaizen.kaizen_savings_calculator import (
    calculate_annual_savings,
    calculate_daily_savings,
    enrich_savings_fields,
    infer_savings_type,
)


def test_infer_savings_type_tempo():
    assert (
        infer_savings_type(
            None,
            seconds_per_occurrence=60,
            occurrences_per_day=10,
            hourly_cost=50,
        )
        == "tempo"
    )


def test_infer_savings_type_qualitativo():
    assert infer_savings_type(None) == "qualitativo"


def test_calculate_daily_savings_tempo():
    daily = calculate_daily_savings(
        {
            "savings_type": "tempo",
            "seconds_per_occurrence": 3600,
            "occurrences_per_day": 1,
            "hourly_cost": 100,
        }
    )
    assert daily == 100.0
    assert calculate_annual_savings(daily) == 36500.0


def test_calculate_daily_savings_material():
    daily = calculate_daily_savings(
        {
            "savings_type": "material",
            "quantity_saved_per_day": 5,
            "unit_material_cost": 12.5,
        }
    )
    assert daily == 62.5


def test_enrich_savings_fields_misto():
    enriched = enrich_savings_fields(
        {
            "branch_code": "01",
            "title": "Teste",
            "seconds_per_occurrence": 60,
            "occurrences_per_day": 10,
            "hourly_cost": 50,
            "quantity_saved_per_day": 2,
            "unit_material_cost": 10,
        }
    )
    assert enriched["savings_type"] == "misto"
    assert enriched["daily_savings"] == pytest.approx(28.33, rel=1e-2)
    assert enriched["annual_savings"] == pytest.approx(10340.45, rel=1e-2)
