"""Real-user retrieval refinement — Commercial + Supplies (no query memorization)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.application.external_capabilities.dynamic_information.text_normalize import (
    normalize_text,
)

_API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _discover(query: str, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    return discover_delpi_information(query=query, top_k=5, actor_id="u1")


def _assert_top(query: str, expected: str, monkeypatch) -> None:
    discovered = _discover(query, monkeypatch)
    assert discovered["eligible_action_count"] == 53, query
    assert discovered["candidates"], query
    assert discovered["candidates"][0]["action_id"] == expected, (
        query,
        [c["action_id"] for c in discovered["candidates"]],
    )


def _alias_blob() -> str:
    allow = load_external_read_allowlist()
    parts: list[str] = []
    for entry in allow.get("operations") or []:
        for alias in entry.get("semanticAliases") or []:
            parts.append(normalize_text(str(alias)))
    return "\n".join(parts)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Como está o OTD dos pedidos de compra este mês?", "get_supplies_purchase_order_otd"),
        ("Qual foi o OTD dos nossos pedidos de compra?", "get_supplies_purchase_order_otd"),
        (
            "Quero ver a evolução semanal do OTD de compras neste mês",
            "get_supplies_purchase_order_otd_series",
        ),
        ("Qual é o valor total do estoque?", "get_supplies_stock_value"),
        ("Quanto vale nosso estoque?", "get_supplies_stock_value"),
        (
            "Quanto economizamos nas negociações de compras?",
            "get_supplies_negotiation_savings_summary",
        ),
        (
            "Qual foi a economia obtida nas negociações?",
            "get_supplies_negotiation_savings_summary",
        ),
        (
            "Quantos materiais estão abaixo do estoque de segurança?",
            "get_supplies_safety_stock_summary",
        ),
        (
            "Quais materiais estão abaixo do estoque de segurança?",
            "get_supplies_safety_stock_items",
        ),
        (
            "Liste os materiais abaixo do estoque de segurança",
            "get_supplies_safety_stock_items",
        ),
        ("Quais produtos estão no depósito 01?", "get_supplies_stock_balances_items"),
        ("Me dê um resumo dos estoques por depósito", "get_supplies_stock_balances_summary"),
        (
            "Quais solicitações de compra estão abertas?",
            "list_supplies_purchase_request_lines",
        ),
        (
            "Me dê um resumo dos materiais em poder de terceiros",
            "get_supplies_third_party_materials_summary",
        ),
        (
            "Quais remessas de materiais para terceiros existem?",
            "get_supplies_third_party_materials_shipments",
        ),
    ],
)
def test_real_user_supplies_top1(query, expected, monkeypatch):
    _assert_top(query, expected, monkeypatch)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Quanto faturamos este mês e qual é a meta?", "get_commercial_rol_summary"),
        ("Qual foi nosso faturamento neste mês?", "get_commercial_rol_summary"),
        (
            "Como o faturamento evoluiu semana a semana neste mês?",
            "get_commercial_rol_series",
        ),
        ("Mostre o faturamento mês a mês", "get_commercial_rol_series"),
        ("Quais clientes mais faturaram este mês?", "get_commercial_rol_by_customer"),
        (
            "Quem são os maiores clientes por faturamento?",
            "get_commercial_rol_by_customer",
        ),
        ("Quais produtos mais faturaram este mês?", "get_commercial_rol_by_product"),
        ("Quais produtos geraram mais faturamento?", "get_commercial_rol_by_product"),
        ("Como está o OTD comercial este mês?", "get_sales_order_otd"),
        ("Qual é o resumo do OTD comercial e a meta?", "get_sales_order_otd_summary"),
        ("Qual o OTD comercial por cliente?", "get_sales_order_otd_by_customer"),
        ("Como ficou o OTD por filial?", "get_sales_order_otd_by_branch"),
        ("Mostre a evolução semanal do OTD comercial", "get_sales_order_otd_series"),
        (
            "Como o OTD comercial evoluiu ao longo dos meses?",
            "get_sales_order_otd_series",
        ),
        ("Qual é a taxa de conversão das propostas?", "get_sales_conversion_rate"),
        (
            "Como a taxa de conversão evoluiu ao longo dos meses?",
            "get_sales_conversion_rate_series",
        ),
        ("Mostre a conversão comercial mês a mês", "get_sales_conversion_rate_series"),
        (
            "Qual a participação de novos negócios no faturamento?",
            "get_new_business_rol_pct",
        ),
        ("Qual é a meta de novos negócios?", "get_new_business_rol_target_pct"),
        ("Quantos clientes novos tivemos em média?", "get_new_clients_average"),
        ("Qual a média mensal de clientes novos?", "get_new_clients_average"),
        ("Quanto do faturamento veio de clientes novos?", "get_new_clients_rol_pct"),
        (
            "Qual a participação dos clientes novos no faturamento?",
            "get_new_clients_rol_pct",
        ),
        ("Como está o ROL da WEG contra a meta?", "get_weg_rol_target_pct"),
        (
            "Qual o atingimento da meta de faturamento da WEG?",
            "get_weg_rol_target_pct",
        ),
    ],
)
def test_real_user_commercial_top1(query, expected, monkeypatch):
    _assert_top(query, expected, monkeypatch)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("OTD comercial", "get_sales_order_otd"),
        ("OTD dos pedidos de compra", "get_supplies_purchase_order_otd"),
        ("evolução do OTD comercial", "get_sales_order_otd_series"),
        ("evolução do OTD de compras", "get_supplies_purchase_order_otd_series"),
        ("estoque do produto 10080001", "get_product_stock"),
        ("valor total do estoque", "get_supplies_stock_value"),
        ("produtos em estoque no depósito 01", "get_supplies_stock_balances_items"),
        ("buscar produto 10080001", "search_products"),
        ("clientes do produto 90260148", "get_product_customers"),
        ("clientes que mais faturaram", "get_commercial_rol_by_customer"),
        ("compras do produto 10080001", "get_product_purchases"),
        ("OTD das compras", "get_supplies_purchase_order_otd"),
    ],
)
def test_real_user_cross_family_top1(query, expected, monkeypatch):
    _assert_top(query, expected, monkeypatch)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # Holdouts: must NOT appear verbatim in semanticAliases.
        (
            "No mês atual, como está o OTD dos pedidos de compra?",
            "get_supplies_purchase_order_otd",
        ),
        ("Preciso do valor agregado do nosso estoque", "get_supplies_stock_value"),
        (
            "Quero o ranking de clientes pelo faturamento do mês",
            "get_commercial_rol_by_customer",
        ),
        (
            "Tem como ver a série temporal da conversão comercial?",
            "get_sales_conversion_rate_series",
        ),
        ("Me diga a média de novos clientes no período", "get_new_clients_average"),
        (
            "Quero os materiais que estão abaixo do estoque de segurança",
            "get_supplies_safety_stock_items",
        ),
    ],
)
def test_real_user_holdouts_not_verbatim_aliases(query, expected, monkeypatch):
    blob = _alias_blob()
    assert normalize_text(query) not in blob, f"holdout memorized in aliases: {query}"
    _assert_top(query, expected, monkeypatch)


@pytest.mark.parametrize(
    "query",
    [
        "altere o estoque de segurança",
        "crie uma solicitação de compra",
        "corrija o OTD",
        "mude a meta comercial",
        "registre um novo cliente",
    ],
)
def test_real_user_write_intent_guard(query, monkeypatch):
    discovered = _discover(query, monkeypatch)
    assert discovered["candidate_count"] == 0, query


def test_allowlist_version_and_eligible_count():
    allow = load_external_read_allowlist()
    assert allow.get("version") == 14
    assert allow.get("coverageDecision", {}).get("taskId") == (
        "DAVI-REAL-USER-RETRIEVAL-REFINEMENT-COMMERCIAL-SUPPLIES-001"
    )
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(eligible) == 53
