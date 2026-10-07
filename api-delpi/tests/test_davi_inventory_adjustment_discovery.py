"""Semantic discovery regression for governed inventory adjustments."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.davi_agent_intelligence_service import (
    DaviAgentIntelligenceService,
)
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

_API_ROOT = Path(__file__).resolve().parents[1]
_ACTOR = "inventory-adjustment-discovery-test"
_SUMMARY = "get_supplies_inventory_adjustments_summary"
_LIST = "list_supplies_inventory_adjustments"


@pytest.fixture(autouse=True)
def _reset_dynamic_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()


def _actions():
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline,
        allowlist=load_external_read_allowlist(),
    )


def _discover(monkeypatch: pytest.MonkeyPatch, query: str):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "discover_service.candidate_token_secret",
        lambda: "inventory-discovery-secret",
    )
    return discover_delpi_information(
        query=query,
        top_k=5,
        actor_id=_ACTOR,
    )


@pytest.mark.parametrize(
    ("query", "expected_first"),
    [
        ("Ajuste de estoque da filial 01 este ano", _SUMMARY),
        ("Qual foi o ajuste líquido do inventário?", _SUMMARY),
        ("Sobra menos furo da filial 01", _SUMMARY),
        ("Valor bruto dos ajustes de estoque", _SUMMARY),
        ("Furo de estoque em 2026", _SUMMARY),
        ("Sobra de inventário por filial", _SUMMARY),
        ("Liste os produtos com ajuste de estoque", _LIST),
        ("Detalhe os lançamentos de inventário", _LIST),
    ],
)
def test_inventory_adjustment_natural_language_routes_first(
    monkeypatch: pytest.MonkeyPatch,
    query: str,
    expected_first: str,
) -> None:
    discovered = _discover(monkeypatch, query)
    assert discovered["candidate_count"] > 0, query
    assert discovered["candidates"][0]["action_id"] == expected_first, query


def test_regression_query_discovers_summary_and_preserves_existing_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovered = _discover(
        monkeypatch,
        (
            "Qual é o ajuste de estoque da filial 01 neste ano de 2026, "
            "de 2026-01-01 a 2026-10-07? Retornar sobra, furo, ajuste bruto "
            "e ajuste líquido."
        ),
    )
    assert discovered["candidate_count"] > 0
    first = discovered["candidates"][0]
    assert first["action_id"] == _SUMMARY

    schema = first["argument_schema"]
    props = schema["properties"]
    assert {"start_date", "end_date", "branch", "warehouse", "product_code", "nature"} <= set(props)
    assert set(schema["required"]) == {"start_date", "end_date"}
    assert props["nature"]["enum"] == ["shortage", "surplus"]
    assert "nature" not in schema["required"]


def test_inventory_adjustment_nature_orchestration_contract() -> None:
    note = DaviAgentIntelligenceService.agent_directives()["flows"]["stock_and_supply"]["note"]
    lowered = note.lower()
    assert "sem nature explícita" in lowered
    assert "pedido de furo → nature=shortage" in lowered
    assert "pedido de sobra → nature=surplus" in lowered
    assert "summary.net_value = surplus_value - shortage_value" in lowered
    assert "nunca apresente gross_value como líquido" in lowered


def test_inventory_adjustment_discovery_aliases_own_gross_quarantine_token() -> None:
    allow = load_external_read_allowlist()
    summary = next(
        op
        for op in allow["operations"]
        if op["operationId"] == _SUMMARY
    )
    aliases = set(summary["semanticAliases"])
    assert "ajuste bruto" in aliases
    assert "valor bruto de ajustes de estoque" in aliases
    assert "movimentação bruta de ajustes" in aliases
    assert "bruto" in set(allow["retrievalQuarantineTokens"])
