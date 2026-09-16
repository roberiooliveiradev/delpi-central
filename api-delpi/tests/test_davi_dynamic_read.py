"""Tests for DAVI dynamic governed READ broker (DAVI-DYNAMIC-READ-002)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.application.external_capabilities.constants import PRODUCT_SEARCH_RESPONSE_FIELDS
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    build_argument_json_schema,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    mint_candidate_token,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_GENERIC_SQL_FORBIDDEN,
    STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE,
    STATUS_WRITE_OUT_OF_SCOPE,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    bound_response_payload,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.domain.ports.davi_catalog_fixed_get_port import CatalogFixedGetResult
from app.interface.mcp.schemas import (
    DiscoverDelpiInformationInput,
    ExecuteDelpiInformationInput,
)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()


def _search_params(*, required_code: bool = False) -> tuple[dict[str, Any], ...]:
    return (
        {"name": "code", "in": "query", "required": required_code, "type": "string"},
        {"name": "description", "in": "query", "required": False, "type": "string"},
        {"name": "group_code", "in": "query", "required": False, "type": "string"},
        {"name": "customer_reference", "in": "query", "required": False, "type": "string"},
        {"name": "page", "in": "query", "required": False, "type": "integer", "minimum": 1},
        {
            "name": "page_size",
            "in": "query",
            "required": False,
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
        },
        {
            "name": "sort",
            "in": "query",
            "required": False,
            "type": "string",
            "enum": ["code", "description"],
        },
    )


def _action(
    *,
    oid: str,
    path: str,
    method: str = "GET",
    status: str = STATUS_DAVI_ELIGIBLE_READ,
    summary: str = "",
    parameters: tuple | None = None,
    execution_mode: str | None = "approved_external_capability",
    approved_response_fields: tuple[str, ...] = PRODUCT_SEARCH_RESPONSE_FIELDS,
) -> TechnicalAction:
    return TechnicalAction(
        action_id=oid,
        operation_id=oid,
        method=method,
        path=path,
        summary=summary or oid.replace("_", " "),
        description="",
        tags=("products",),
        davi_status=status,
        entity="product",
        shape="paged_list",
        parameters=parameters if parameters is not None else _search_params(),
        searchable_text=f"{oid} {summary} {path} products".lower(),
        execution_mode=execution_mode,
        approved_response_fields=approved_response_fields,
    )


def test_allowlist_is_search_products_only():
    allow = load_external_read_allowlist()
    ids = load_allowlist_operation_ids(allow)
    assert ids == {"search_products"}
    assert allow.get("version") == 2
    not_approved = {
        (x.get("operationId") if isinstance(x, dict) else x)
        for x in (allow.get("explicitlyNotApproved") or [])
    }
    assert "get_product_summary" in not_approved
    assert "get_product_detail" in not_approved


def test_classify_hard_blocks():
    allow = {"search_products"}
    assert (
        classify_operation(
            method="GET",
            path="/data/sql",
            operation_id="run_sql",
            allowlisted_operation_ids=allow,
        )
        == STATUS_GENERIC_SQL_FORBIDDEN
    )
    assert (
        classify_operation(
            method="POST",
            path="/products",
            operation_id="create_product",
            allowlisted_operation_ids=allow,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids=allow,
        )
        == STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/search",
            operation_id="search_products",
            allowlisted_operation_ids=allow,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/summary",
            operation_id="get_product_summary",
            allowlisted_operation_ids=allow,
        )
        != STATUS_DAVI_ELIGIBLE_READ
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}",
            operation_id="get_product_detail",
            allowlisted_operation_ids=allow,
        )
        != STATUS_DAVI_ELIGIBLE_READ
    )


def test_inventory_eligible_count_is_one():
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads(
        (root / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    actions = build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )
    assert len(actions) == int(baseline.get("operation_count") or 0)
    eligible = [a for a in actions if a.executable]
    assert len(eligible) == 1
    assert eligible[0].operation_id == "search_products"


def test_discover_rejects_transport_smuggling_in_schema():
    with pytest.raises(ValidationError):
        DiscoverDelpiInformationInput.model_validate(
            {"query": "estoque", "path": "/products/x/stock"}
        )
    with pytest.raises(ValidationError):
        ExecuteDelpiInformationInput.model_validate(
            {"candidate_token": "x", "url": "https://evil"}
        )


def test_discover_requires_actor(monkeypatch):
    set_actions_for_tests(
        [_action(oid="search_products", path="/products/search", summary="search products")]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    with pytest.raises(CandidateTokenError):
        discover_delpi_information(query="search products", top_k=5, actor_id=None)
    with pytest.raises(CandidateTokenError):
        discover_delpi_information(query="search products", top_k=5, actor_id="")


def test_discover_eligible_only_search_products(monkeypatch):
    set_actions_for_tests(
        [
            _action(
                oid="search_products",
                path="/products/search",
                summary="search products master",
            ),
            _action(
                oid="get_product_detail",
                path="/products/{code}",
                summary="product detail",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="get_product_summary",
                path="/products/{code}/summary",
                summary="product summary stock prices",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="get_product_stock",
                path="/products/{code}/stock",
                summary="product stock",
                status=STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE,
                execution_mode=None,
                approved_response_fields=(),
            ),
            _action(
                oid="run_sql",
                path="/data/sql",
                summary="sql",
                status=STATUS_GENERIC_SQL_FORBIDDEN,
                execution_mode=None,
                approved_response_fields=(),
            ),
        ]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="product", top_k=10, actor_id="u1")
    assert discovered["eligible_action_count"] == 1
    action_ids = {c["action_id"] for c in discovered["candidates"]}
    assert action_ids == {"search_products"}
    assert "get_product_summary" not in action_ids
    assert "get_product_detail" not in action_ids


def test_discover_and_execute_happy_path_approved_projection(monkeypatch):
    set_actions_for_tests(
        [
            _action(
                oid="search_products",
                path="/products/search",
                summary="search products master",
            ),
        ]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="search products", top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 1
    token = discovered["candidates"][0]["candidate_token"]
    schema = discovered["candidates"][0]["argument_schema"]
    assert schema["additionalProperties"] is False
    assert "customer_reference" not in schema["properties"]

    def runner(**kwargs):
        assert kwargs.get("code") == "A"
        return {
            "items": [
                {
                    "product_code": "A",
                    "description": "Widget",
                    "group_category": "G1",
                    "cost": 99.9,  # must not leak even if runner misbehaves
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "A"},
        actor_id="u1",
        search_products_runner=runner,
    )
    assert result["status"] == "ok"
    assert result["truncated"] is False
    assert "http_status" not in result
    item = result["data"]["items"][0]
    assert set(item.keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)
    assert "cost" not in item


def test_actor_token_binding(monkeypatch):
    action = _action(oid="search_products", path="/products/search")
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token_a = mint_candidate_token(
        action_id="search_products", actor_id="user-a", secret=secret, ttl_seconds=60
    )
    # same actor OK (parse)
    parse_candidate_token(token_a, secret=secret, expected_actor_id="user-a")
    # other actor DENY
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token_a, secret=secret, expected_actor_id="user-b")
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id="user-b",
            search_products_runner=lambda **_: {"items": []},
        )
    # missing actor DENY
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id=None,
            search_products_runner=lambda **_: {"items": []},
        )
    # empty actor in mint DENY
    with pytest.raises(CandidateTokenError):
        mint_candidate_token(
            action_id="search_products", actor_id="", secret=secret, ttl_seconds=60
        )
    # expired DENY
    expired = mint_candidate_token(
        action_id="search_products",
        actor_id="user-a",
        secret=secret,
        ttl_seconds=1,
        now=1.0,
    )
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(
            expired, secret=secret, expected_actor_id="user-a", now=100.0
        )
    # forged DENY
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token_a + "x", secret=secret, expected_actor_id="user-a")


def test_argument_validation_matrix():
    action = _action(
        oid="search_products",
        path="/products/search",
        parameters=_search_params(),
    )
    path_action = TechnicalAction(
        action_id="get_demo",
        operation_id="get_demo",
        method="GET",
        path="/demo/{code}",
        summary="demo",
        description="",
        tags=(),
        davi_status=STATUS_DAVI_ELIGIBLE_READ,
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
            {
                "name": "mode",
                "in": "query",
                "required": True,
                "type": "string",
                "enum": ["a", "b"],
            },
            {"name": "page", "in": "query", "required": False, "type": "integer"},
        ),
        searchable_text="get_demo",
        execution_mode="catalog_get",
        approved_response_fields=("x",),
    )

    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"url": "https://evil"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"operationId": "get_product_stock"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"customer_reference": "x"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"unknown_arg": "x"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"page_size": "nope"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"mode": "a"})  # missing path code
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1"})  # missing required query
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1", "mode": "z"})  # wrong enum

    ok = validate_arguments(action, {"description": "motor", "page": 2, "page_size": "10"})
    assert ok["page"] == 2
    assert ok["page_size"] == 10
    assert isinstance(ok["page"], int)

    schema_disc = build_argument_json_schema(action)
    schema_exec = build_argument_json_schema(action)
    assert schema_disc == schema_exec


def test_execute_rejects_unauthorized_without_auth_on_catalog_get(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_get",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="future_read", actor_id="u1", secret=secret, ttl_seconds=60
    )
    port = MagicMock()
    with pytest.raises(PermissionError):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "X"},
            actor_id="u1",
            authorization=None,
            catalog_get_port=port,
        )
    port.execute.assert_not_called()


def test_bounded_payload_is_not_field_authorization():
    fat = {
        "items": [{"product_code": "A", "secret_cost": 1, "description": "d"}],
        "page": 1,
    }
    bounded = bound_response_payload(fat, max_bytes=65536, max_items=50)
    assert "secret_cost" in bounded["data"]["items"][0]
    projected = apply_approved_field_projection(
        fat, approved_fields=PRODUCT_SEARCH_RESPONSE_FIELDS
    )
    assert set(projected["items"][0].keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)


def test_hmac_dedicated_secret_precedence(monkeypatch):
    from app.application.external_capabilities.dynamic_information import content_loader
    import app.config as cfg

    class _Dedicated:
        DAVI_CANDIDATE_HMAC_SECRET = "dedicated-hmac"
        JWT_SECRET = "jwt-fallback"

    class _Fallback:
        DAVI_CANDIDATE_HMAC_SECRET = ""
        JWT_SECRET = "jwt-fallback"

    monkeypatch.setattr(cfg, "settings", _Dedicated())
    assert content_loader.candidate_token_secret() == "dedicated-hmac"
    monkeypatch.setattr(cfg, "settings", _Fallback())
    assert content_loader.candidate_token_secret() == "jwt-fallback"


def test_metamorphic_rename_preserves_retrieval():
    a1 = _action(
        oid="search_products",
        path="/products/search",
        summary="buscar produtos cadastro",
    )
    a2 = _action(
        oid="product_master_lookup_v2",
        path="/v2/catalog/items",
        summary="buscar produtos cadastro",
    )
    hits1 = retrieve_eligible_actions("buscar produtos", [a1], top_k=3)
    hits2 = retrieve_eligible_actions("buscar produtos", [a2], top_k=3)
    assert hits1 and hits2
    assert hits1[0][0].operation_id != hits2[0][0].operation_id


def test_dynamic_information_application_has_no_http_transport():
    root = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information"
    )
    forbidden_calls = ("client.get(", "TestClient", "response.json", "http_status")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "app.composition" not in text, path.name
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("fastapi"), path.name
                assert not node.module.startswith("httpx"), path.name
                assert "testclient" not in node.module.lower(), path.name
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "fastapi" not in alias.name, path.name
                    assert "httpx" not in alias.name, path.name
        if path.name == "governed_http_executor.py":
            continue
        for needle in forbidden_calls:
            assert needle not in text, f"{path.name} contains {needle}"
        assert 'headers["Authorization"]' not in text, path.name
        assert "Authorization=" not in text, path.name


def test_catalog_get_port_outcome_mapping(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_get",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="future_read", actor_id="u1", secret=secret, ttl_seconds=60
    )
    port = MagicMock()
    port.execute.return_value = CatalogFixedGetResult(
        outcome="ok", payload={"items": [{"name": "N", "secret": 1}]}
    )
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "X"},
        actor_id="u1",
        authorization="Bearer t",
        catalog_get_port=port,
    )
    assert result["data"]["items"][0] == {"name": "N"}
    port.execute.assert_called_once()
