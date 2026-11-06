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
