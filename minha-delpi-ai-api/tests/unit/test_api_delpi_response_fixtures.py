"""Smoke: fixtures Fase 0 carregam envelope api-delpi válido."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_data,
    load_api_delpi_fixture,
)

BASELINE_FIXTURES = [
    "product_search.json",
    "product_detail_90269001.json",
    "product_summary_90269001.json",
    "product_stock_90269001.json",
    "product_structure_90269001.json",
    "product_analyser_90269001.json",
    "product_factory_status_90269002.json",
    "product_production_status_90269002.json",
    "product_shipping_status_90269002.json",
    "product_structure_exclusivity_90269002.json",
    "product_raw_material_price_intelligence_10080001.json",
    "product_cost_impact_simulation_90261255.json",
    "product_last_purchase_10080001.json",
    "supplies_cpv.json",
]

FICTIONAL_PA_CODE = "90269001"


@pytest.mark.parametrize("fixture_name", BASELINE_FIXTURES)
def test_api_delpi_fixture_has_success_envelope(fixture_name: str) -> None:
    envelope = load_api_delpi_fixture(fixture_name)
    assert envelope.get("success") is True
    assert "data" in envelope
    assert envelope["data"] is not None


def test_api_delpi_fixtures_directory_has_at_least_eight_files() -> None:
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures" / "api_delpi_responses"
    json_files = sorted(fixtures_dir.glob("*.json"))
    assert len(json_files) >= 8


def test_product_stock_fixture_data_shape() -> None:
    data = load_api_delpi_data("product_stock_90269001.json")
    assert "items" in data
    assert data["items"][0]["product_code"] == FICTIONAL_PA_CODE
    assert data["items"][0]["product_code"].startswith("9026")
    assert "available_quantity" in data["items"][0]
