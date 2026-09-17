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
    assert result["eligible_action_count"] == 15


@pytest.mark.parametrize(
    "query",
    [
        "descricao do produto",
        "estoque atualizado do produto",
        "data de atualizacao do produto",
        "produto alterado",
        "status de aprovacao",
        "ultima alteracao do produto",
    ],
)
def test_noun_participle_does_not_trigger_write_guard(query):
    assert has_explicit_write_intent(query) is False


@pytest.mark.parametrize(
    ("query", "action_id"),
    [
        ("produto 10080055", "search_products"),
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
    assert result["eligible_action_count"] == 15


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
        "search_products",
        "get_product_stock",
        "get_product_suppliers",
        "get_product_customers",
        "get_product_purchases",
        "get_product_structure",
        "get_product_production_status",
        "get_product_factory_status",
        "get_product_structure_exclusivity",
        "get_product_shipping_status",
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
        "get_product_guide",
        "get_product_parents",
    }
