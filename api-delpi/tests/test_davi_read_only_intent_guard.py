"""DAVI READ-only explicit write-intent discovery guard (not AuthZ)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
    has_explicit_write_intent,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)

_BASELINE = (
    Path(__file__).resolve().parents[1] / "app" / "content" / "openapi_baseline.json"
)
_ACTOR = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(autouse=True)
def _seed():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    actions = build_technical_actions_from_baseline(
        json.loads(_BASELINE.read_text(encoding="utf-8")),
        allowlist=load_external_read_allowlist(),
    )
    set_actions_for_tests(actions)
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


@pytest.mark.parametrize(
    "query",
    [
        "altere o produto 10080055",
        "alterar o produto 10080055",
        "atualize o produto 10080055",
        "edite o produto 10080055",
        "exclua o produto 10080055",
        "crie um produto",
        "cadastre um produto",
        "remova o produto 10080055",
        "salve a alteração do produto",
        "delete the product 10080055",
        "update the product 10080055",
        "edit the product 10080055",
        "pode alterar o produto 10080055",
        "por favor altere o produto 10080055",
        "quero alterar o produto 10080055",
        "preciso atualizar o produto 10080055",
        "gostaria de editar o produto 10080055",
        "please update the product",
        "can you delete the product",
        "altere o status fabril do produto",
        "atualize a expedição do produto",
        "cadastre exclusividade de MP",
        "insira um novo fornecedor",
        "inserir um novo fornecedor",
        "insira o item 10080055",
        "inclua um registro",
        "incluir um registro",
    ],
)
def test_explicit_write_intent_returns_zero_candidates(query, monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    assert has_explicit_write_intent(query) is True
    result = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    assert result["candidate_count"] == 0
    assert result["candidates"] == []
    assert result["eligible_action_count"] == 87


@pytest.mark.parametrize(
    "query",
    [
        "descricao do produto",
        "estoque atualizado do produto",
        "data de atualizacao do produto",
        "produto alterado",
        "status de aprovacao",
        "ultima alteracao do produto",
        "inserção de fornecedor",
        "insercao de fornecedor",
        "item inserido recentemente",
        "produto inserido no cadastro",
        "inclusão de itens do pedido",
    ],
)
def test_noun_participle_does_not_trigger_write_guard(query):
    assert has_explicit_write_intent(query) is False


@pytest.mark.parametrize(
    "query",
    [
        "gere o DANFE da nota fiscal 12345",
        "gerar o relatório mensal",
        "calcule o ICMS da nota de saída",
        "calcular o imposto da nota",
        "monte a escala de férias do time",
        "montar a escala de produção",
        "traduza a descrição do produto para inglês",
        "traduzir a descrição",
        "emita a nota fiscal 12345",
        "emitir o relatório de vendas",
    ],
)
def test_non_read_command_verbs_return_zero_candidates(query, monkeypatch):
    """Imperative commands that produce content (generate/calculate/emit)
    are outside the read-only broker even though they are not mutations."""
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    assert has_explicit_write_intent(query) is True
    result = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    assert result["candidate_count"] == 0
    assert result["candidates"] == []
    assert result["eligible_action_count"] == 87


@pytest.mark.parametrize(
    ("query", "action_id"),
    [
        ("buscar produto 10080055", "search_products"),
        ("estoque do produto 10080055", "get_product_stock"),
        ("fornecedores do produto 10080055", "get_product_suppliers"),
        ("clientes do produto 10080055", "get_product_customers"),
        ("compras do produto 10080055", "get_product_purchases"),
        ("estrutura do produto 10080055", "get_product_structure"),
        ("status de produção do produto 10080055", "get_product_production_status"),
    ],
)
def test_read_queries_still_retrieve(query, action_id, monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    assert has_explicit_write_intent(query) is False
    result = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    assert result["candidate_count"] >= 1
    assert result["candidates"][0]["action_id"] == action_id
    assert result["eligible_action_count"] == 87


def test_bare_product_query_is_ambiguous_but_not_write(monkeypatch):
    """Bare "produto X" is semantically ambiguous: search_products ties
    lexically with other product actions and must not deterministically own
    the intent — it only needs to remain a top candidate."""
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    assert has_explicit_write_intent("produto 10080055") is False
    result = discover_delpi_information(
        query="produto 10080055", top_k=5, actor_id=_ACTOR
    )
    assert result["candidate_count"] >= 1
    ids = [c["action_id"] for c in result["candidates"]]
    assert "search_products" in ids


def test_guard_runs_before_ranking():
    actions = build_technical_actions_from_baseline(
        json.loads(_BASELINE.read_text(encoding="utf-8")),
        allowlist=load_external_read_allowlist(),
    )
    ranked = retrieve_eligible_actions(
        "altere o produto 10080055",
        actions,
        top_k=10,
    )
    assert ranked == []


def test_guard_config_is_not_authz_and_eligible_unchanged():
    allow = load_external_read_allowlist()
    guard = allow.get("retrievalReadOnlyGuard") or {}
    assert "NOT AuthZ" in str(guard.get("description") or "")
    assert load_allowlist_operation_ids(allow) == {
        "get_commercial_rol_by_branch",
        "get_commercial_rol_by_customer",
        "get_commercial_rol_by_product",
        "get_commercial_rol_series",
        "get_commercial_rol_summary",
        "get_new_business_rol_pct",
        "get_new_business_rol_target_pct",
        "get_new_clients_average",
        "get_new_clients_rol_pct",
        "get_on_time_delivery_pct",
        "get_overall_equipment_effectiveness_pct",
        "get_product_customers",
        "get_product_drawing",
        "get_product_factory_status",
        "get_product_guide",
        "get_product_inbound_invoice_items",
        "get_product_internal_movements",
        "get_product_last_purchase",
        "get_product_outbound_invoice_items",
        "get_product_parents",
        "get_product_pricing",
        "get_product_production_status",
        "get_product_purchase_price_history",
        "get_product_purchases",
        "get_product_raw_material_set_shortages",
        "get_product_sales_open_orders",
        "get_product_sales_summary",
        "get_product_shipping_status",
        "get_product_stock",
        "get_product_structure",
        "get_product_structure_exclusivity",
        "get_product_suppliers",
        "get_production_allocation_gaps",
        "get_production_appointments_produced_totals",
        "get_production_appointments_summary",
        "get_production_consumption_by_item",
        "get_production_consumption_top_items",
        "get_production_losses_records",
        "get_production_losses_top_materials",
        "get_production_machine_load_operations",
        "get_production_machine_load_work_centers",
        "get_production_oee",
        "get_production_oee_series",
        "get_production_orders_finished_without_consumption",
        "get_production_otd",
        "get_production_otd_series",
        "get_protheus_table",
        "get_sales_conversion_rate",
        "get_sales_conversion_rate_series",
        "get_sales_order_otd",
        "get_sales_order_otd_by_branch",
        "get_sales_order_otd_by_customer",
        "get_sales_order_otd_series",
        "get_sales_order_otd_series_by_customer",
        "get_sales_order_otd_summary",
        "get_supplies_cpv",
        "get_supplies_inventory_adjustments_summary",
        "get_supplies_inventory_turnover",
        "get_supplies_negotiation_savings_summary",
        "get_supplies_otd",
        "get_supplies_purchase_order_otd",
        "get_supplies_purchase_order_otd_series",
        "get_supplies_safety_stock_consumption_analysis_item_details",
        "get_supplies_safety_stock_consumption_analysis_items",
        "get_supplies_safety_stock_consumption_analysis_summary",
        "get_supplies_safety_stock_item_details",
        "get_supplies_safety_stock_item_suppliers",
        "get_supplies_safety_stock_items",
        "get_supplies_safety_stock_summary",
        "get_supplies_safety_stock_supplier_purchase_price_history",
        "get_supplies_stock_balances_items",
        "get_supplies_stock_balances_summary",
        "get_supplies_stock_value",
        "get_supplies_third_party_materials_shipments",
        "get_supplies_third_party_materials_summary",
        "get_weg_rol_target_pct",
        "list_exclusive_raw_materials_catalog",
        "list_product_drawings",
        "list_product_inventory_blocks",
        "list_product_physical_locations",
        "list_production_order_operation_materials",
        "list_protheus_table_columns",
        "list_supplies_inventory_adjustments",
        "list_supplies_purchase_request_lines",
        "search_products",
        "search_products_by_supplier_part_number",
        "search_protheus_columns_by_description",
        "search_protheus_columns_in_table",
        "search_tables_by_description",
    }
