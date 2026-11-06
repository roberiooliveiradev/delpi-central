"""Product Master remains discoverable/executable after MCP tool surface simplification."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_RESPONSE_FIELDS,
    SEARCH_PRODUCTS_OPERATION_ID,
)
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
from app.application.models.page import Page
from app.interface.mcp.server import create_mcp_server

_API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )
def test_search_products_remains_allowlisted_and_eligible():
    allow = load_external_read_allowlist()
    ids = {o["operationId"] for o in allow["operations"]}
    assert SEARCH_PRODUCTS_OPERATION_ID in ids
    assert len(ids) == 97
    assert any(a.operation_id == SEARCH_PRODUCTS_OPERATION_ID and a.executable for a in _actions())
