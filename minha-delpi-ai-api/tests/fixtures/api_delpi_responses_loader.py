"""Carrega fixtures JSON do envelope api-delpi (Fase 0 baseline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURES_DIR = Path(__file__).resolve().parent / "api_delpi_responses"


def load_api_delpi_fixture(name: str) -> dict[str, Any]:
    path = _FIXTURES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Fixture api-delpi não encontrada: {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Fixture inválida (esperado objeto JSON): {name}")
    return payload


def load_api_delpi_data(name: str) -> Any:
    envelope = load_api_delpi_fixture(name)
    return envelope.get("data")


def with_api_delpi_meta(envelope: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    payload = dict(envelope)
    payload["meta"] = meta
    return payload


PRODUCT_ENTITY_META: dict[str, dict[str, Any]] = {
    "product_stock_90269001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_stock",
        "entity": "product_stock",
        "shape": "paged_list",
        "fields": {
            "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
        },
    },
    "product_structure_90269001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_structure",
        "entity": "product_structure",
        "shape": "hierarchy",
    },
    "product_analyser_90269001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_analyser",
        "entity": "product_analyser",
        "shape": "composite_analysis",
    },
    "product_factory_status_90269002.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_factory_status",
        "entity": "product_factory_status",
        "shape": "composite_analysis",
    },
    "product_production_status_90269002.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_production_status",
        "entity": "product_production_status",
        "shape": "playbook_report",
    },
    "product_shipping_status_90269002.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_shipping_status",
        "entity": "product_shipping_status",
        "shape": "playbook_report",
    },
    "product_structure_exclusivity_90269002.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_structure_exclusivity",
        "entity": "product_structure_exclusivity",
        "shape": "playbook_report",
    },
    "product_structure_exclusivity_90261805.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_structure_exclusivity",
        "entity": "product_structure_exclusivity",
        "shape": "playbook_report",
    },
    "product_raw_material_price_intelligence_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_raw_material_price_intelligence",
        "entity": "product_raw_material_price_intelligence",
        "shape": "composite_analysis",
    },
    "product_raw_material_price_intelligence_10080022.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_raw_material_price_intelligence",
        "entity": "product_raw_material_price_intelligence",
        "shape": "composite_analysis",
    },
    "product_cost_impact_simulation_90261255.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_cost_impact_simulation",
        "entity": "product_cost_impact_simulation",
        "shape": "composite_analysis",
    },
    "product_last_purchase_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_last_purchase",
        "entity": "product_last_purchase",
        "shape": "playbook_report",
    },
    "product_pricing_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_pricing",
        "entity": "product_pricing",
        "shape": "scalar",
    },
    "product_purchase_price_history_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_purchase_price_history",
        "entity": "product_purchase_price_history",
        "shape": "playbook_report",
    },
    "product_purchase_budget_history_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_purchase_budget_history",
        "entity": "product_purchase_budget_history",
        "shape": "playbook_report",
    },
    "product_purchases_10080001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_purchases",
        "entity": "product_purchases",
        "shape": "paged_list",
    },
    "product_detail_90269001.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_detail",
        "entity": "product",
        "shape": "product_snapshot",
    },
    "product_directives_90260882.json": {
        "dataVersion": "2026-06",
        "operationId": "get_product_directives",
        "entity": "product_directives",
        "shape": "composite_analysis",
    },
    "product_search.json": {
        "dataVersion": "2026-06",
        "operationId": "search_products",
        "entity": "product_search",
        "shape": "paged_list",
    },
    "production_consumption_top_items.json": {
        "dataVersion": "2026-06",
        "operationId": "get_production_consumption_top_items",
        "entity": "production_consumption_top_items",
        "shape": "playbook_report",
    },
    "production_schedule_today_20260622.json": {
        "dataVersion": "2026-06",
        "operationId": "get_production_schedule_today",
        "entity": "production_schedule_today",
        "shape": "playbook_report",
    },
    "supplies_cpv.json": {
        "dataVersion": "2026-06",
        "operationId": "get_supplies_cpv",
        "entity": "supplies_cpv",
        "shape": "scalar",
    },
    "supplies_safety_stock_item_details_10020113.json": {
        "dataVersion": "2026-06",
        "operationId": "get_supplies_safety_stock_item_details",
        "entity": "supplies_safety_stock_detail",
        "shape": "composite_analysis",
    },

    "data_sql_rows.json": {
        "dataVersion": "2026-06",
        "operationId": "execute_readonly_sql",
        "entity": "sql",
        "shape": "paged_list",
    },
}


def load_api_delpi_fixture_with_meta(name: str) -> dict[str, Any]:
    envelope = load_api_delpi_fixture(name)
    meta = PRODUCT_ENTITY_META.get(name)

    if not meta:
        return envelope

    return with_api_delpi_meta(envelope, meta)
