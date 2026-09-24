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
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
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


def test_mcp_surface_is_exactly_two_tools_without_search_products():
    import asyncio

    tools = asyncio.run(create_mcp_server().list_tools())
    names = [t.name for t in tools]
    assert names == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert SEARCH_PRODUCTS_OPERATION_ID not in names


def test_search_products_remains_allowlisted_and_eligible():
    allow = load_external_read_allowlist()
    ids = {o["operationId"] for o in allow["operations"]}
    assert SEARCH_PRODUCTS_OPERATION_ID in ids
    assert len(ids) == 63
    assert any(a.operation_id == SEARCH_PRODUCTS_OPERATION_ID and a.executable for a in _actions())


@pytest.mark.parametrize(
    ("query", "expect_top1"),
    [
        ("qual a descrição do produto 10090043", True),
        ("buscar produto 10080022", True),
        ("qual o grupo do produto 10080001", True),
        # Bare "produto <code>" is intentionally weaker; search_products must still rank.
        ("produto 10080055", False),
    ],
)
def test_product_master_queries_discover_search_products(query, expect_top1, monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["eligible_action_count"] == 63
    assert discovered["candidates"]
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert SEARCH_PRODUCTS_OPERATION_ID in ids
    if expect_top1:
        assert ids[0] == SEARCH_PRODUCTS_OPERATION_ID


def test_search_products_executes_via_generic_broker(monkeypatch):
    set_actions_for_tests(_actions())
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(
        query="qual a descrição do produto 10090043",
        top_k=5,
        actor_id="u1",
    )
    token = discovered["candidates"][0]["candidate_token"]
    product = MagicMock()
    product.to_dict.return_value = {
        "code": "10090043",
        "description": "TRAVA 3VIAS MOLEX",
        "group_code": "1009",
        "customer_reference": "secret",
    }
    mock_uc = MagicMock()
    mock_uc.execute.return_value = Page(
        items=[product], total=1, page=1, page_size=50
    )

    def runner(**kwargs):
        from app.application.external_capabilities.product_search_service import (
            search_products,
        )

        kwargs.pop("enforce_authz", None)
        kwargs.pop("tool_name", None)
        return search_products(
            search_use_case=mock_uc,
            enforce_authz=False,
            **kwargs,
        )

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "10090043"},
        actor_id="u1",
        search_products_runner=runner,
    )
    assert result["status"] == "ok"
    assert result["action_id"] == SEARCH_PRODUCTS_OPERATION_ID
    item = result["data"]["items"][0]
    assert set(item.keys()) <= set(PRODUCT_SEARCH_RESPONSE_FIELDS)
    assert item["product_code"] == "10090043"
    assert item["description"] == "TRAVA 3VIAS MOLEX"
    assert item["group_category"] == "1009"
    assert "customer_reference" not in item
