"""Tests for DAVI dynamic governed READ broker (DAVI-DYNAMIC-READ-002/003)."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call

import pytest
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_INPUT_FIELDS,
    PRODUCT_SEARCH_RESPONSE_FIELDS,
)
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
    STATUS_NEEDS_NESTED_PROJECTION_SUPPORT,
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
from app.application.external_capabilities.dynamic_information.execution_plan import (
    CatalogActionPlan,
    build_execution_plan,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    bound_response_payload,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
    CatalogActionExecutorPort,
)
from app.infrastructure.davi.asgi_catalog_action_executor import AsgiCatalogActionExecutor
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
    approved_input_fields: tuple[str, ...] | None = None,
    semantic_aliases: tuple[str, ...] = (),
) -> TechnicalAction:
    summary_text = summary or oid.replace("_", " ")
    aliases = semantic_aliases
    if approved_input_fields is None:
        input_fields = (
            PRODUCT_SEARCH_INPUT_FIELDS if oid == "search_products" else ()
        )
    else:
        input_fields = approved_input_fields
    searchable = f"{oid} {summary_text} {path} products {' '.join(aliases)}".lower()
    return TechnicalAction(
        action_id=oid,
        operation_id=oid,
        method=method,
        path=path,
        summary=summary_text,
        description="",
        tags=("products",),
        davi_status=status,
        entity="product",
        shape="paged_list",
        parameters=parameters if parameters is not None else _search_params(),
        searchable_text=searchable,
        execution_mode=execution_mode,
        approved_response_fields=approved_response_fields,
        approved_input_fields=input_fields,
        semantic_aliases=aliases,
    )


def _load_governed_search_products() -> TechnicalAction:
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads(
        (root / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    actions = build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )
    action = next(a for a in actions if a.operation_id == "search_products")
    assert action.executable
    return action


def test_allowlist_is_search_products_only():
    allow = load_external_read_allowlist()
    ids = load_allowlist_operation_ids(allow)
    assert ids == {"search_products"}
    assert allow.get("version") == 4
    assert allow.get("coverageDecision", {}).get("decision") == "PROMOTE_ZERO_NEW_OPERATIONS"
    entry = next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == "search_products"
    )
    assert set(entry["approvedInputFields"]) == set(PRODUCT_SEARCH_INPUT_FIELDS)
    assert entry.get("semanticAliases")
    blocked = {
        x["operationId"]: x.get("primaryBlocker")
        for x in allow.get("explicitlyNotApproved") or []
        if isinstance(x, dict)
    }
    assert blocked["get_product_stock"] == "NEEDS_BRANCH_AUTHZ_EVIDENCE"
    assert blocked["get_product_detail"] == "NEEDS_NESTED_PROJECTION_SUPPORT"
    assert blocked["get_product_summary"] == "NEEDS_DATA_CLASSIFICATION"
    assert blocked["get_product_pricing"] == "NEEDS_DATA_CLASSIFICATION"
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
            shape="product_snapshot",
        )
        == STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
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
    # Coverage expansion did not invent approvals.
    assert set(a.operation_id for a in eligible) == {"search_products"}


def test_high_value_product_ops_remain_quarantined_from_discovery(monkeypatch):
    actions = build_technical_actions_from_baseline(
        json.loads(
            (
                Path(__file__).resolve().parents[1] / "app/content/openapi_baseline.json"
            ).read_text(encoding="utf-8")
        ),
        allowlist=load_external_read_allowlist(),
    )
    set_actions_for_tests(actions)
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    for query in (
        "estoque do produto 10080055",
        "estrutura do produto 10080055",
        "preço do produto 10080055",
        "fornecedor do produto",
        "cliente do produto",
        "status de produção do produto",
    ):
        discovered = discover_delpi_information(query=query, top_k=10, actor_id="u1")
        assert discovered["eligible_action_count"] == 1
        assert discovered["candidate_count"] == 0, query
        action_ids = {c["action_id"] for c in discovered["candidates"]}
        assert not action_ids & {
            "get_product_stock",
            "get_product_detail",
            "get_product_summary",
            "get_product_structure",
            "get_product_pricing",
            "get_product_suppliers",
            "get_product_customers",
            "get_product_factory_status",
        }


def test_three_tool_invariant_and_generic_path_not_applicable_without_new_ops():
    import asyncio
    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    # No newly eligible non-search op → generic catalog proof NOT_APPLICABLE.
    assert load_allowlist_operation_ids(load_external_read_allowlist()) == {
        "search_products"
    }


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
                    "cost": 99.9,
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
    parse_candidate_token(token_a, secret=secret, expected_actor_id="user-a")
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token_a, secret=secret, expected_actor_id="user-b")
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id="user-b",
            search_products_runner=lambda **_: {"items": []},
        )
    with pytest.raises(CandidateTokenError):
        execute_delpi_information(
            candidate_token=token_a,
            arguments={},
            actor_id=None,
            search_products_runner=lambda **_: {"items": []},
        )
    with pytest.raises(CandidateTokenError):
        mint_candidate_token(
            action_id="search_products", actor_id="", secret=secret, ttl_seconds=60
        )
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
        execution_mode="catalog_action",
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
        validate_arguments(path_action, {"mode": "a"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(path_action, {"code": "1", "mode": "z"})

    ok = validate_arguments(action, {"description": "motor", "page": 2, "page_size": "10"})
    assert ok["page"] == 2
    assert ok["page_size"] == 10
    assert isinstance(ok["page"], int)
    assert build_argument_json_schema(action) == build_argument_json_schema(action)


def test_catalog_action_plan_is_transport_neutral():
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    plan = build_execution_plan(action, {"code": "X"})
    assert isinstance(plan, CatalogActionPlan)
    assert plan.action_id == "future_read"
    assert plan.validated_arguments == {"code": "X"}
    assert not hasattr(plan, "request")
    assert "method" not in plan.__dataclass_fields__
    assert "path" not in plan.__dataclass_fields__
    assert "query" not in plan.__dataclass_fields__


def test_semantic_executor_port_contract_and_binding(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
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

    received: dict[str, Any] = {}

    class RecordingExecutor:
        def execute(
            self,
            *,
            action_id: str,
            validated_arguments: dict[str, Any],
        ) -> CatalogActionExecutionResult:
            received["action_id"] = action_id
            received["validated_arguments"] = validated_arguments
            received["kwargs_keys"] = sorted(
                inspect.signature(self.execute).parameters.keys()
            )
            return CatalogActionExecutionResult(
                outcome="ok", payload={"items": [{"name": "N", "secret": 1}]}
            )

    executor = RecordingExecutor()
    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "X"},
        actor_id="u1",
        catalog_action_executor=executor,
    )
    assert received["action_id"] == "future_read"
    assert received["validated_arguments"] == {"code": "X"}
    assert "authorization" not in received["kwargs_keys"]
    assert "method" not in received["kwargs_keys"]
    assert "path" not in received["kwargs_keys"]
    assert result["data"]["items"][0] == {"name": "N"}

    # Application execute_delpi_information signature must not accept authorization.
    params = inspect.signature(execute_delpi_information).parameters
    assert "authorization" not in params
    assert "http_client" not in params
    assert "catalog_get_port" not in params


def test_catalog_executor_maps_unauthorized_and_forbidden(monkeypatch):
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
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

    class UnauthorizedExecutor:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="unauthorized")

    class ForbiddenExecutor:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="forbidden")

    with pytest.raises(PermissionError, match="Unauthorized"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "X"},
            actor_id="u1",
            catalog_action_executor=UnauthorizedExecutor(),
        )
    with pytest.raises(PermissionError, match="Forbidden"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "X"},
            actor_id="u1",
            catalog_action_executor=ForbiddenExecutor(),
        )


def test_infrastructure_resolves_catalog_and_auth_header():
    action = _action(
        oid="synthetic_catalog_read",
        path="/synthetic/{item_id}",
        parameters=(
            {"name": "item_id", "in": "path", "required": True, "type": "string"},
            {"name": "include", "in": "query", "required": False, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("label",),
    )
    set_actions_for_tests([action])

    client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": [{"label": "ok", "secret": 9}]}
    client.get.return_value = resp

    executor = AsgiCatalogActionExecutor(client, authorization="Bearer user-token")
    result = executor.execute(
        action_id="synthetic_catalog_read",
        validated_arguments={"item_id": "42", "include": "meta"},
    )
    assert result.outcome == "ok"
    client.get.assert_called_once_with(
        "/synthetic/42",
        params={"include": "meta"},
        headers={"Authorization": "Bearer user-token"},
    )


def test_infrastructure_denies_unknown_non_eligible_and_non_get():
    set_actions_for_tests(
        [
            _action(
                oid="blocked_read",
                path="/blocked",
                status="NEEDS_EXTERNAL_PROCESSING_APPROVAL",
                execution_mode="catalog_action",
                approved_response_fields=("x",),
                parameters=(),
            ),
            _action(
                oid="write_like",
                path="/write",
                method="POST",
                execution_mode="catalog_action",
                approved_response_fields=("x",),
                parameters=(),
            ),
        ]
    )
    client = MagicMock()
    executor = AsgiCatalogActionExecutor(client, authorization="Bearer t")

    unknown = executor.execute(action_id="does_not_exist", validated_arguments={})
    assert unknown.outcome == "error"
    assert "Unknown" in (unknown.error_message or "")

    blocked = executor.execute(action_id="blocked_read", validated_arguments={})
    assert blocked.outcome == "forbidden"

    non_get = executor.execute(action_id="write_like", validated_arguments={})
    assert non_get.outcome == "error"
    assert "GET" in (non_get.error_message or "")
    client.get.assert_not_called()


def test_infrastructure_maps_http_401_403_to_semantic_outcomes():
    action = _action(
        oid="future_read",
        path="/future/{code}",
        parameters=(
            {"name": "code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("name",),
    )
    set_actions_for_tests([action])
    client = MagicMock()

    resp401 = MagicMock()
    resp401.status_code = 401
    resp401.json.return_value = {"detail": "no"}
    client.get.return_value = resp401
    out401 = AsgiCatalogActionExecutor(client, authorization="Bearer t").execute(
        action_id="future_read", validated_arguments={"code": "X"}
    )
    assert out401.outcome == "unauthorized"

    resp403 = MagicMock()
    resp403.status_code = 403
    resp403.json.return_value = {"detail": "no"}
    client.get.return_value = resp403
    out403 = AsgiCatalogActionExecutor(client, authorization="Bearer t").execute(
        action_id="future_read", validated_arguments={"code": "X"}
    )
    assert out403.outcome == "forbidden"


def test_metamorphic_catalog_action_without_endpoint_specific_code(monkeypatch):
    """Different action_id/path/params execute via the same generic adapter."""
    synthetic = _action(
        oid="demo_widget_lookup",
        path="/widgets/{widget_code}/info",
        parameters=(
            {"name": "widget_code", "in": "path", "required": True, "type": "string"},
            {"name": "locale", "in": "query", "required": False, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("title",),
        summary="demo widget lookup",
    )
    # Not on production allowlist — only injected for this test index.
    set_actions_for_tests([synthetic])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="demo_widget_lookup", actor_id="u1", secret=secret, ttl_seconds=60
    )

    client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": [{"title": "W", "internal_cost": 1}]}
    client.get.return_value = resp
    bound = AsgiCatalogActionExecutor(client, authorization="Bearer actor-a")

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"widget_code": "W-9", "locale": "pt-BR"},
        actor_id="u1",
        catalog_action_executor=bound,
    )
    assert result["data"]["items"][0] == {"title": "W"}
    assert client.get.call_args == call(
        "/widgets/W-9/info",
        params={"locale": "pt-BR"},
        headers={"Authorization": "Bearer actor-a"},
    )
    # No production allowlist pollution.
    assert "demo_widget_lookup" not in load_allowlist_operation_ids(
        load_external_read_allowlist()
    )


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


def _assert_no_http_transport_in_tree(root: Path) -> None:
    """Structural dependency check — not naive comment/deny-list text search."""
    forbidden_modules = ("fastapi", "httpx", "starlette.testclient")
    paths = [root] if root.is_file() else list(root.rglob("*.py"))
    for path in paths:
        if path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                assert not any(
                    mod == f or mod.startswith(f + ".") for f in forbidden_modules
                ), f"{path}: imports {mod}"
                assert "testclient" not in mod.lower(), path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "fastapi" not in alias.name
                    assert "httpx" not in alias.name
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "get":
                    if isinstance(func.value, ast.Name) and func.value.id in {
                        "client",
                        "http_client",
                        "response",
                    }:
                        raise AssertionError(
                            f"{path}: forbidden call {func.value.id}.get"
                        )
                if isinstance(func, ast.Attribute) and func.attr == "json":
                    if isinstance(func.value, ast.Name) and func.value.id == "response":
                        raise AssertionError(f"{path}: forbidden response.json()")
            if isinstance(node, ast.Attribute) and node.attr == "status_code":
                raise AssertionError(f"{path}: references status_code")
            if isinstance(node, ast.Name) and node.id in {
                "CatalogFixedGetRequest",
                "TestClient",
            }:
                raise AssertionError(f"{path}: references {node.id}")
            if isinstance(node, ast.arg) and node.arg == "authorization":
                raise AssertionError(f"{path}: parameter authorization")


def test_domain_and_application_have_zero_http_transport_dependency():
    api_root = Path(__file__).resolve().parents[1] / "app"
    _assert_no_http_transport_in_tree(
        api_root / "domain" / "ports" / "davi_catalog_action_executor_port.py"
    )
    _assert_no_http_transport_in_tree(
        api_root / "application" / "external_capabilities" / "dynamic_information"
    )
    port_src = (
        api_root / "domain" / "ports" / "davi_catalog_action_executor_port.py"
    ).read_text(encoding="utf-8")
    assert "CatalogFixedGetRequest" not in port_src
    assert "Literal[\"GET\"]" not in port_src
    assert "client.get" not in port_src
    assert "status_code" not in port_src
    # Port must not model transport Authorization as an execute parameter (AST covers this).
    assert "def execute" in port_src


def test_catalog_action_executor_port_is_protocol_compatible():
    assert hasattr(CatalogActionExecutorPort, "execute")


# --- DAVI-DYNAMIC-READ-004: PT-BR retrieval + schema fidelity + outputSchema ---


@pytest.mark.parametrize(
    "query",
    [
        "produto",
        "produtos",
        "buscar produto",
        "buscar o produto 10080055 pelo código",
        "Buscar o produto 10080055 pelo codigo",
        "qual a descrição do produto 10080055",
        "qual a descricao do produto 10080055",
        "qual o grupo do produto 10080055",
        "search products",
        "PRODUTO",
        "  produto!!  ",
    ],
)
def test_ptbr_positive_retrieval(query, monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] >= 1, (
        f"query={query!r} candidate_count={discovered['candidate_count']}"
    )
    assert discovered["candidates"][0]["action_id"] == "search_products"


@pytest.mark.parametrize(
    "query",
    [
        "estoque do produto 10080055",
        "saldo disponível do produto 10080055",
        "preço do produto 10080055",
        "preco do produto 10080055",
        "fornecedor do produto 10080055",
        "cliente do produto",
        "qual o clima hoje",
        "escreva um e-mail",
        "qual é a hora",
        "resuma este texto",
        "financeiro",
    ],
)
def test_negative_retrieval_quarantine(query, monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="u1")
    assert discovered["candidate_count"] == 0, (
        f"query={query!r} unexpectedly returned {discovered['candidates']}"
    )
    assert discovered["eligible_action_count"] == 1


def test_search_products_discovery_schema_matches_approved_input(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="produto", top_k=3, actor_id="u1")
    schema = discovered["candidates"][0]["argument_schema"]
    assert set(schema["properties"].keys()) == set(PRODUCT_SEARCH_INPUT_FIELDS)
    assert schema["additionalProperties"] is False
    for forbidden in ("sort", "direction", "customer_reference"):
        assert forbidden not in schema["properties"]
    # Same schema used by execution validation.
    assert build_argument_json_schema(action)["properties"].keys() == schema[
        "properties"
    ].keys()


def test_unknown_and_unapproved_arguments_denied():
    action = _load_governed_search_products()
    for bad in (
        {"url": "https://evil"},
        {"sort": "code"},
        {"direction": "desc"},
        {"customer_reference": "x"},
        {"unknown": "y"},
    ):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, bad)


def test_execution_parity_passes_pagination_to_runner(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="search_products", actor_id="u1", secret=secret, ttl_seconds=60
    )
    captured: dict[str, Any] = {}

    def runner(**kwargs):
        captured.update(kwargs)
        return {
            "items": [
                {
                    "product_code": "10080055",
                    "description": "TERM",
                    "group_category": "1008",
                    "cost": 1,
                }
            ],
            "page": kwargs.get("page"),
            "page_size": kwargs.get("page_size"),
            "total": 1,
            "total_pages": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={
            "code": "10080055",
            "description": "TERM",
            "group_code": "1008",
            "page": 2,
            "page_size": 10,
        },
        actor_id="u1",
        search_products_runner=runner,
    )
    assert captured["code"] == "10080055"
    assert captured["description"] == "TERM"
    assert captured["group_code"] == "1008"
    assert captured["page"] == 2
    assert captured["page_size"] == 10
    assert result["projection"] == "approved_fields"
    assert set(result["data"]["items"][0].keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)


def test_live_like_ptbr_discover_execute_flow(monkeypatch):
    action = _load_governed_search_products()
    set_actions_for_tests([action])
    secret = "test-secret-davi"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: secret,
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    discovered = discover_delpi_information(
        query="Buscar o produto 10080055 pelo código",
        top_k=5,
        actor_id="u1",
    )
    assert discovered["candidate_count"] == 1
    assert discovered["candidates"][0]["action_id"] == "search_products"
    token = discovered["candidates"][0]["candidate_token"]

    def runner(**kwargs):
        assert kwargs["code"] == "10080055"
        return {
            "items": [
                {
                    "product_code": "10080055",
                    "description": "TERM. FASTON",
                    "group_category": "1008",
                    "internal": True,
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        }

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "10080055"},
        actor_id="u1",
        search_products_runner=runner,
    )
    assert result["status"] == "ok"
    assert result["projection"] == "approved_fields"
    assert len(result["data"]["items"]) == 1
    assert set(result["data"]["items"][0].keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)


def test_synthetic_semantic_alias_generalization(monkeypatch):
    synthetic = _action(
        oid="demo_widget_lookup",
        path="/widgets/{widget_code}",
        parameters=(
            {"name": "widget_code", "in": "path", "required": True, "type": "string"},
        ),
        execution_mode="catalog_action",
        approved_response_fields=("title",),
        approved_input_fields=("widget_code",),
        semantic_aliases=("consultar widget", "buscar widget"),
        summary="demo widget lookup",
    )
    set_actions_for_tests([synthetic])
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    discovered = discover_delpi_information(
        query="consultar widget", top_k=3, actor_id="u1"
    )
    assert discovered["candidate_count"] == 1
    assert discovered["candidates"][0]["action_id"] == "demo_widget_lookup"
    assert "demo_widget_lookup" not in load_allowlist_operation_ids(
        load_external_read_allowlist()
    )


def test_mcp_output_schemas_present_for_all_three_tools():
    import asyncio
    from app.interface.mcp.server import create_mcp_server
    from app.interface.mcp.schemas import (
        DiscoverDelpiInformationOutput,
        ExecuteDelpiInformationOutput,
        SearchProductsOutput,
        discover_delpi_information_output_json_schema,
        execute_delpi_information_output_json_schema,
        search_products_output_json_schema,
    )

    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 3
    by_name = {t.name: t for t in tools}
    assert by_name["search_products"].outputSchema == search_products_output_json_schema()
    assert (
        by_name["discover_delpi_information"].outputSchema
        == discover_delpi_information_output_json_schema()
    )
    assert (
        by_name["execute_delpi_information"].outputSchema
        == execute_delpi_information_output_json_schema()
    )

    # Runtime envelopes validate against output models.
    DiscoverDelpiInformationOutput.model_validate(
        {
            "query": "produto",
            "top_k": 5,
            "candidate_count": 1,
            "eligible_action_count": 1,
            "candidates": [
                {
                    "candidate_token": "x.y",
                    "description": "Search products",
                    "semantic_hints": {"entity": "product", "shape": "paged_list", "tags": []},
                    "required_arguments": [],
                    "argument_schema": {"type": "object", "properties": {}},
                    "pagination_hints": {
                        "supports_page": True,
                        "supports_page_size": True,
                    },
                    "retrieval_score": 0.8,
                    "action_id": "search_products",
                }
            ],
        }
    )
    ExecuteDelpiInformationOutput.model_validate(
        {
            "action_id": "search_products",
            "status": "ok",
            "entity": "product",
            "shape": "paged_list",
            "projection": "approved_fields",
            "data": {"items": []},
            "truncated": False,
            "is_complete": True,
            "response_bytes": 12,
        }
    )
    SearchProductsOutput.model_validate(
        {
            "items": [
                {
                    "product_code": "A",
                    "description": "d",
                    "group_category": "g",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        }
    )


def test_no_hardcoded_portuguese_phrase_to_operation_id_map():
    root = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information"
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert '"produto": "search_products"' not in text
        assert "'produto': 'search_products'" not in text
        assert "if \"produto\" in query" not in text
        assert "if 'produto' in query" not in text
