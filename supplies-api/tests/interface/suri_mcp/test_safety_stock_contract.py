"""SURI-MCP — safety_stock filter contract hardening.

The wire schema must publish the closed vocabularies the BFF owner
already enforces (``safety_stock_service``), so MCP agents construct
valid arguments without a ``read(safety_stock,filters)`` round-trip.
Enum values are asserted against the canonical frozensets — never a
second hardcoded list.
"""

import asyncio
import json

import pytest
from pydantic import ValidationError

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.safety_stock_service import (
    ALLOWED_SORT_DIRECTIONS,
    ALLOWED_SORT_FIELDS,
    ALLOWED_STATUSES,
    BRANCH_SCOPES,
)
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    SafetyStockItemIdentity,
    SafetyStockItemsFilters,
)
from app.interfaces.mcp.server import suri_mcp_server


def _enum_values(prop: dict) -> set:
    values: set = set()
    nodes = [prop, *prop.get("anyOf", [])]
    for node in nodes:
        for value in node.get("enum") or []:
            if value is not None:
                values.add(value)
    return values


@pytest.fixture(scope="module")
def read_defs() -> dict:
    tools = asyncio.run(suri_mcp_server.list_tools())
    read_tool = next(tool for tool in tools if tool.name == "read")
    return read_tool.input_schema["$defs"]


class _User:
    is_superadmin = True
    access_token = "tok"

    def has_permission(self, code):
        return True


def _ok(result) -> bool:
    return getattr(result, "is_error", getattr(result, "isError", False)) is False


class TestPublishedEnums:
    def test_status_enum_matches_owner_vocabulary(self, read_defs):
        expected = set(ALLOWED_STATUSES)
        for name in ("SafetyStockSummaryFilters", "SafetyStockItemsFilters"):
            prop = read_defs[name]["properties"]["status"]
            assert _enum_values(prop) == expected

    def test_branch_scope_enum_matches_owner_vocabulary(self, read_defs):
        expected = set(BRANCH_SCOPES)
        for name in (
            "SafetyStockScopeFilters",
            "SafetyStockSummaryFilters",
            "SafetyStockItemsFilters",
        ):
            prop = read_defs[name]["properties"]["branch"]
            assert _enum_values(prop) == expected

    def test_identity_branch_enum_is_concrete_units(self, read_defs):
        prop = read_defs["SafetyStockItemIdentity"]["properties"]["branch"]
        assert _enum_values(prop) == set(OPERATIONAL_UNITS)

    def test_sort_enums_match_owner_vocabulary(self, read_defs):
        props = read_defs["SafetyStockItemsFilters"]["properties"]
        assert _enum_values(props["sortBy"]) == set(ALLOWED_SORT_FIELDS)
        assert _enum_values(props["sortDirection"]) == set(
            ALLOWED_SORT_DIRECTIONS
        )


class TestModelValidation:
    @pytest.mark.parametrize("value", sorted(ALLOWED_STATUSES))
    def test_canonical_status_values_accepted(self, value):
        model = SafetyStockItemsFilters.model_validate(
            {"branch": "01", "status": value}
        )
        assert model.status == value

    def test_short_status_alias_rejected(self):
        with pytest.raises(ValidationError):
            SafetyStockItemsFilters.model_validate(
                {"branch": "01", "status": "below"}
            )

    def test_omitted_status_preserves_none_semantics(self):
        model = SafetyStockItemsFilters.model_validate({"branch": "01"})
        assert model.status is None

    def test_identity_branch_requires_concrete_unit(self):
        SafetyStockItemIdentity.model_validate(
            {"code": "M001", "branch": "01"}
        )
        with pytest.raises(ValidationError):
            SafetyStockItemIdentity.model_validate(
                {"code": "M001", "branch": "all"}
            )


class TestDispatchDepthValidation:
    """Dict payloads bypass SDK argument validation — the service must
    still reject invalid values in depth (defense in depth unchanged)."""

    def test_invalid_status_dict_still_rejected_by_service(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            tool_bridge, "_effective_user", lambda: _User()
        )
        result = tool_bridge.tool_read(
            "safety_stock", "items", {"branch": "01", "status": "below"}
        )
        assert not _ok(result)
        payload = json.loads(result.content[0].text)
        assert payload["status_code"] == 422
        assert payload["code"] == "ARGUMENT_VALIDATION"

    def test_valid_status_dict_reaches_service(self, monkeypatch):
        calls = {}

        class _Service:
            def list_items(self, user, **kwargs):
                calls.update(kwargs)
                return {"ok": True}

        monkeypatch.setattr(
            tool_bridge, "_effective_user", lambda: _User()
        )
        monkeypatch.setattr(
            tool_bridge, "_SAFETY_STOCK_SERVICE", _Service()
        )
        result = tool_bridge.tool_read(
            "safety_stock",
            "items",
            {"branch": "01", "status": "below_safety_stock",
             "page": 1, "page_size": 3},
        )
        assert _ok(result), result
        assert calls["status"] == "below_safety_stock"
        assert calls["branch"] == "01"
