"""DAVI Product Master security prerequisites (SEC-01 / SEC-02).

Non-productive security-governance coverage only:
  SEC-01 — product.sales.open_orders re-scoped to canonical PVA permission +
           portfolio scope enforced before summary/pagination.
  SEC-02 — governed semantic READ POST mechanism (SEMANTIC_READ_POST opt-in),
           catalog-fixed transport, validated JSON body contract.

No productive allowlist mutation: fixtures are synthetic.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

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
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
    build_technical_actions_from_openapi,
)
from app.application.external_capabilities.dynamic_information.constants import (
    SEMANTIC_TRANSPORT_READ_POST,
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_DESTRUCTIVE_OUT_OF_SCOPE,
    STATUS_NEEDS_BOUNDED_EXECUTION,
    STATUS_WRITE_OUT_OF_SCOPE,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
    PortfolioScope,
)
from app.domain.entities.product.product_sales_open_orders import (
    ProductSalesOpenOrders,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)
from app.infrastructure.davi.asgi_catalog_action_executor import (
    AsgiCatalogActionExecutor,
)
from app.infrastructure.persistence.totvs.product_repositories.product_sales_open_orders_repository import (
    ProductSalesOpenOrdersRepository,
)
import app.interface.http.routes.product_routes as product_routes

_ACTOR = "11111111-1111-4111-8111-111111111111"
_SECRET = "test-secret-davi-product-master-sec"
_CLAIMS = {
    "sub": _ACTOR,
    "email": "davi-sec@example.com",
    "aud": "delpi-central",
    "name": "DAVI Security",
}


# ---------------------------------------------------------------------------
# SEC-01 — product sales open orders: canonical PVA AuthZ + portfolio scope
# ---------------------------------------------------------------------------


def _fake_user(*, permissions: list[str], is_superadmin: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = _ACTOR
    user.sub = _ACTOR
    user.email = "davi-sec@example.com"
    user.is_superadmin = is_superadmin
    user.permissions = list(permissions)
    user.rbac_unavailable = False
    return user


def _open_orders_payload() -> ProductSalesOpenOrders:
    return ProductSalesOpenOrders(
        items=[
            {
                "branch": "01",
                "order_number": "000123",
                "order_item": "01",
                "customer_code": "000001",
                "customer_store": "01",
                "customer_name": "ACME",
                "open_quantity": 16.0,
                "unit_price": 575.13,
                "open_value": 9202.08,
                "delivery_date": "2026-09-30",
                "issue_date": "2026-08-01",
            }
        ],
        quantity=16.0,
        value=9202.08,
        orders=1,
        page=1,
        page_size=50,
        total=1,
        total_pages=1,
    )


@contextmanager
def _open_orders_route_fakes(
    *,
    user: MagicMock,
    scope: PortfolioScope | None = None,
) -> Iterator[dict[str, Any]]:
    """Route-level wiring: real authz decorators + real portfolio helpers.

    Only persistence-facing builders are faked (no DB in tests); the canonical
    scope use case is replaced with a capture fake that records its inputs.
    """
    use_case = MagicMock()
    use_case.execute.return_value = _open_orders_payload().as_payload()
    scope_uc = MagicMock()
    scope_uc.execute.return_value = scope or PortfolioScope(
        unrestricted=True,
        seller_id=None,
        allowed_customers=None,
        empty_portfolio=False,
        message=None,
    )
    user_id = str(getattr(user, "id", "") or "")

    async def _rbac(_token: str) -> dict[str, Any]:
        return {
            "id": user_id,
            "email": user.email,
            "name": "DAVI Security",
            "roles": [],
            "groups": [],
            "permissions": list(user.permissions),
            "is_superadmin": bool(user.is_superadmin),
            "rbac_unavailable": False,
        }

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                product_routes,
                "build_get_product_sales_open_orders",
                return_value=use_case,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_resolve_portfolio_scope_use_case",
                return_value=scope_uc,
            )
        )
        stack.enter_context(
            patch("delpi_auth.jwt_validator.validate_token", return_value=_CLAIMS)
        )
        stack.enter_context(
            patch(
                "delpi_auth.middleware.fastapi_auth.validate_token",
                return_value=_CLAIMS,
            )
        )
        stack.enter_context(
            patch(
                "app.middleware.auth_middleware.validate_token",
                return_value=_CLAIMS,
            )
        )
        stack.enter_context(
            patch("delpi_auth.authorization.resolve_user_context", return_value=user)
        )
        stack.enter_context(
            patch(
                "delpi_auth.middleware.fastapi_auth.load_user_rbac",
                side_effect=_rbac,
            )
        )
        stack.enter_context(
            patch(
                "app.startup.run_plugins_migrations_on_startup.run_plugins_migrations_on_startup",
                lambda: None,
            )
        )
        stack.enter_context(
            patch(
                "app.startup.schedule_openapi_consumer_notify.schedule_openapi_consumer_notify_on_startup",
                lambda: None,
            )
        )
        yield {"use_case": use_case, "scope_uc": scope_uc}


def _get_open_orders() -> Any:
    from app.main import app

    # No `with`: lifespan re-entry would re-run the MCP session manager once-only.
    client = TestClient(app)
    return client.get(
        "/products/90262910/sales/open-orders",
        headers={"Authorization": "Bearer end-user-token"},
    )


def test_sec01_api_delpi_access_only_is_forbidden() -> None:
    """AUTHZ-01: api-delpi.access alone must NOT authorize open-orders."""
    user = _fake_user(permissions=["api-delpi.access"])
    with _open_orders_route_fakes(user=user) as fakes:
        response = _get_open_orders()
    assert response.status_code == 403
    fakes["use_case"].execute.assert_not_called()
    fakes["scope_uc"].execute.assert_not_called()


def test_sec01_canonical_pva_permission_reaches_use_case() -> None:
    """AUTHZ-02: canonical pedidos-venda-abertos permission proceeds."""
    user = _fake_user(permissions=["pedidos-venda-abertos.access"])
    with _open_orders_route_fakes(user=user) as fakes:
        response = _get_open_orders()
    assert response.status_code == 200
    fakes["scope_uc"].execute.assert_called_once()
    call = fakes["scope_uc"].execute.call_args
    assert call.kwargs["user_id"] == _ACTOR
    assert call.kwargs["is_unrestricted"] is False  # no commercial.manage
    assert "seller_id_filter" not in call.kwargs
    fakes["use_case"].execute.assert_called_once()
    scope = fakes["use_case"].execute.call_args.kwargs["scope"]
    assert scope.unrestricted is True


def test_sec01_route_forwards_restricted_scope_to_use_case() -> None:
    """Restricted portfolio → the route hands the canonical scope downstream."""
    user = _fake_user(permissions=["pedidos-venda-abertos.access"])
    restricted = PortfolioScope(
        unrestricted=False,
        seller_id="s1",
        allowed_customers=frozenset({("000001", "01")}),
        empty_portfolio=False,
        message=None,
    )
    with _open_orders_route_fakes(user=user, scope=restricted) as fakes:
        response = _get_open_orders()
    assert response.status_code == 200
    scope = fakes["use_case"].execute.call_args.kwargs["scope"]
    assert scope.unrestricted is False
    assert scope.allowed_customers == frozenset({("000001", "01")})


def _capture_sql_repository() -> tuple[ProductSalesOpenOrdersRepository, dict]:
    repo = ProductSalesOpenOrdersRepository()
    captured: dict[str, Any] = {}

    # `with self` resolves __enter__ on the class; neutralize the DB touchpoints.
    repo._connect = lambda: None
    repo._close = lambda **kwargs: None

    def fake_one(sql, params=()):
        captured["summary_sql"] = sql
        captured["summary_params"] = params
        return {
            "open_quantity": 16.0,
            "open_value": 9202.08,
            "orders": 1,
            "line_count": 1,
        }

    def fake_query(sql, params=()):
        captured["items_sql"] = sql
        captured["items_params"] = params
        return []

    repo.execute_one = fake_one
    repo.execute_query = fake_query
    return repo, captured


def test_sec01_restricted_scope_constrains_summary_and_items_sql() -> None:
    """AUTHZ-03: allowed customers are a SQL constraint before summary/pagination."""
    allowed = frozenset({("000001", "01"), ("000002", "02")})
    repo, captured = _capture_sql_repository()

    repo.get_sales_open_orders(
        "90262910", page=1, page_size=50, allowed_customers=allowed
    )

    for key in ("summary_sql", "items_sql"):
        sql = captured[key]
        assert "C5.C5_CLIENTE" in sql
        assert "C5.C5_LOJACLI" in sql
        assert sql.count("(LTRIM(RTRIM(C5.C5_CLIENTE)) = ? AND LTRIM(RTRIM(C5.C5_LOJACLI)) = ?)") == 2
    params = captured["summary_params"]
    assert params[0] == "90262910"
    assert list(params[1:]) == ["000001", "01", "000002", "02"]


def test_sec01_unrestricted_scope_adds_no_customer_clause() -> None:
    repo, captured = _capture_sql_repository()
    repo.get_sales_open_orders("90262910", allowed_customers=None)
    assert "C5.C5_CLIENTE" not in captured["summary_sql"]
    assert captured["summary_params"] == ("90262910",)


def test_sec01_empty_portfolio_scope_forces_empty_result() -> None:
    """Restricted scope with zero customers → fail-closed empty dataset."""
    repo, captured = _capture_sql_repository()
    repo.get_sales_open_orders("90262910", allowed_customers=frozenset())
    assert "1 = 0" in captured["summary_sql"]
    assert "1 = 0" in captured["items_sql"]


def test_sec01_branch_narrows_but_never_expands_scope() -> None:
    """AUTHZ-04: branch filter composes with — never replaces — customer scope."""
    allowed = frozenset({("000001", "01")})
    repo, captured = _capture_sql_repository()
    repo.get_sales_open_orders(
        "90262910", branch="02", allowed_customers=allowed
    )
    sql = captured["summary_sql"]
    assert "C6.C6_FILIAL = ?" in sql
    assert "C5.C5_CLIENTE" in sql
    params = captured["summary_params"]
    assert params == ("90262910", "02", "000001", "01")


def test_sec01_use_case_forwards_allowed_customers() -> None:
    from app.application.use_cases.product.get_product_sales_open_orders_use_case import (
        GetProductSalesOpenOrdersUseCase,
    )
    from app.application.dto.product.get_product_sales_open_orders_request import (
        GetProductSalesOpenOrdersRequest,
    )

    repository = MagicMock()
    repository.get_sales_open_orders.return_value = _open_orders_payload()
    use_case = GetProductSalesOpenOrdersUseCase(repository=repository)
    scope = PortfolioScope(
        unrestricted=False,
        seller_id="s1",
        allowed_customers=frozenset({("000001", "01")}),
        empty_portfolio=False,
        message=None,
    )
    use_case.execute(
        GetProductSalesOpenOrdersRequest(code="90262910"), scope=scope
    )
    assert repository.get_sales_open_orders.call_args.kwargs[
        "allowed_customers"
    ] == frozenset({("000001", "01")})


def test_sec01_use_case_unrestricted_scope_sends_none() -> None:
    from app.application.use_cases.product.get_product_sales_open_orders_use_case import (
        GetProductSalesOpenOrdersUseCase,
    )
    from app.application.dto.product.get_product_sales_open_orders_request import (
        GetProductSalesOpenOrdersRequest,
    )

    repository = MagicMock()
    repository.get_sales_open_orders.return_value = _open_orders_payload()
    use_case = GetProductSalesOpenOrdersUseCase(repository=repository)
    scope = PortfolioScope(
        unrestricted=True,
        seller_id=None,
        allowed_customers=None,
        empty_portfolio=False,
        message=None,
    )
    use_case.execute(
        GetProductSalesOpenOrdersRequest(code="90262910"), scope=scope
    )
    assert (
        repository.get_sales_open_orders.call_args.kwargs["allowed_customers"]
        is None
    )


# ---------------------------------------------------------------------------
# SEC-02 — governed semantic READ POST (SEMANTIC_READ_POST)
# ---------------------------------------------------------------------------

_PHYSICAL_LOCATIONS_OPENAPI: dict[str, Any] = {
    "openapi": "3.1.0",
    "paths": {
        "/products/physical-locations": {
            "post": {
                "operationId": "list_product_physical_locations",
                "summary": "Physical pickup locations in batch",
                "tags": ["products"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/PhysicalLocationsBatchRequest"
                            }
                        }
                    },
                },
            }
        }
    },
    "components": {
        "schemas": {
            "PhysicalLocationsBatchRequest": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "minLength": 2, "maxLength": 2},
                    "product_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["branch"],
            }
        }
    },
}

_GOV_FIXTURE_ALLOWLIST: dict[str, Any] = {
    "operations": [
        {
            "operationId": "list_product_physical_locations",
            "semanticTransport": SEMANTIC_TRANSPORT_READ_POST,
            "approvedInputFields": ["branch", "product_codes"],
            "approvedResponseFields": ["product_code", "branch", "physical_location"],
            "argumentConstraints": {
                "requireArguments": ["branch", "product_codes"],
                "argumentLimits": {"product_codes": {"minItems": 1, "maxItems": 50}},
            },
        },
        {
            "operationId": "list_product_inventory_blocks",
            "semanticTransport": SEMANTIC_TRANSPORT_READ_POST,
            "approvedInputFields": ["branch", "product_codes", "warehouse"],
            "approvedResponseFields": [
                "product_code",
                "warehouse",
                "inventory_blocked",
            ],
            "argumentConstraints": {
                "requireArguments": ["branch", "product_codes"],
                "argumentLimits": {
                    "product_codes": {"minItems": 1, "maxItems": 50},
                    "warehouse": {"default": "01"},
                },
            },
        },
    ]
}


def _post_action(
    *,
    operation_id: str = "list_product_physical_locations",
    semantic_transport: str | None = SEMANTIC_TRANSPORT_READ_POST,
    request_body: Any | None = "__default__",
    davi_status: str = STATUS_DAVI_ELIGIBLE_READ,
    method: str = "POST",
    path: str = "/products/physical-locations",
    approved_inputs: tuple[str, ...] = ("branch", "product_codes"),
    constraints: dict[str, Any] | None = None,
) -> TechnicalAction:
    if request_body == "__default__":
        request_body = {
            "properties": {
                "branch": {"type": "string", "minLength": 2, "maxLength": 2},
                "product_codes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ("branch",),
            "supported": True,
        }
    return TechnicalAction(
        action_id=operation_id,
        operation_id=operation_id,
        method=method,
        path=path,
        summary="fixture",
        description="fixture",
        tags=("products",),
        davi_status=davi_status,
        approved_response_fields=("product_code", "physical_location"),
        approved_input_fields=approved_inputs,
        argument_constraints=constraints
        or {
            "requireArguments": ["branch", "product_codes"],
            "argumentLimits": {"product_codes": {"minItems": 1, "maxItems": 50}},
        },
        semantic_transport=semantic_transport,
        request_body=request_body,
    )


def _classify(
    *,
    method: str,
    path: str,
    operation_id: str | None,
    allowlist: dict[str, Any],
    request_body_supported: bool | None = None,
) -> str:
    return classify_operation(
        method=method,
        path=path,
        operation_id=operation_id,
        allowlisted_operation_ids=load_allowlist_operation_ids(allowlist),
        allowlist=allowlist,
        request_body_supported=request_body_supported,
    )


def test_sec02_marked_allowlisted_post_is_eligible() -> None:
    """POST-01: explicit governance + allowlist + projections + supported body."""
    status = _classify(
        method="POST",
        path="/products/physical-locations",
        operation_id="list_product_physical_locations",
        allowlist=_GOV_FIXTURE_ALLOWLIST,
        request_body_supported=True,
    )
    assert status == STATUS_DAVI_ELIGIBLE_READ


def test_sec02_post_without_marker_is_write() -> None:
    """POST-02: same operation without semantic-read governance → WRITE."""
    bare = {
        "operations": [
            {
                "operationId": "list_product_physical_locations",
                "approvedInputFields": ["branch", "product_codes"],
                "approvedResponseFields": ["product_code"],
            }
        ]
    }
    assert (
        _classify(
            method="POST",
            path="/products/physical-locations",
            operation_id="list_product_physical_locations",
            allowlist=bare,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )


def test_sec02_marker_without_allowlist_is_write() -> None:
    """Marker alone is insufficient — operation must be allowlisted too."""
    assert (
        _classify(
            method="POST",
            path="/products/physical-locations",
            operation_id="list_product_physical_locations",
            allowlist={"operations": []},
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )


def test_sec02_arbitrary_post_is_write() -> None:
    """POST-03."""
    assert (
        _classify(
            method="POST",
            path="/products/anything",
            operation_id="some_unrelated_post",
            allowlist=_GOV_FIXTURE_ALLOWLIST,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_sec02_put_patch_are_write(method: str) -> None:
    """POST-04/05."""
    assert (
        _classify(
            method=method,
            path="/products/x",
            operation_id="update_whatever",
            allowlist=_GOV_FIXTURE_ALLOWLIST,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )


def test_sec02_delete_is_destructive() -> None:
    """POST-06."""
    assert (
        _classify(
            method="DELETE",
            path="/products/x",
            operation_id="delete_whatever",
            allowlist=_GOV_FIXTURE_ALLOWLIST,
        )
        == STATUS_DESTRUCTIVE_OUT_OF_SCOPE
    )


def test_sec02_openapi_body_normalization_resolves_local_ref() -> None:
    """Trusted requestBody normalization resolves the local component schema."""
    actions = build_technical_actions_from_openapi(
        _PHYSICAL_LOCATIONS_OPENAPI, allowlist=_GOV_FIXTURE_ALLOWLIST
    )
    action = actions[0]
    assert action.davi_status == STATUS_DAVI_ELIGIBLE_READ
    assert action.semantic_transport == SEMANTIC_TRANSPORT_READ_POST
    body = action.request_body or {}
    assert body.get("supported") is True
    assert set(body["properties"]) == {"branch", "product_codes"}
    assert body["properties"]["product_codes"]["type"] == "array"
    assert body["required"] == ("branch",)
    assert action.body_fields == frozenset({"branch", "product_codes"})


def test_sec02_argument_schema_contains_body_fields_only_approved() -> None:
    action = _post_action()
    schema = build_argument_json_schema(action)
    assert set(schema["properties"]) == {"branch", "product_codes"}
    assert schema["properties"]["product_codes"]["maxItems"] == 50
    assert schema["properties"]["product_codes"]["minItems"] == 1
    assert set(schema["required"]) == {"branch", "product_codes"}


@pytest.mark.parametrize(
    "key",
    ["method", "path", "url", "host", "operationId", "authorization"],
)
def test_sec02_transport_arguments_rejected(key: str) -> None:
    """POST-07/08: caller can never supply transport or identity controls."""
    action = _post_action()
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action,
            {"branch": "01", "product_codes": ["A"], key: "evil"},
        )


def test_sec02_unknown_body_field_rejected_before_execution() -> None:
    """POST-09."""
    action = _post_action()
    with pytest.raises(ArgumentValidationError, match="Unknown argument"):
        validate_arguments(
            action,
            {"branch": "01", "product_codes": ["A"], "extra": 1},
        )


@pytest.mark.parametrize(
    "count,ok",
    [(0, False), (1, True), (50, True), (51, False)],
)
def test_sec02_product_codes_bounds(count: int, ok: bool) -> None:
    """POST-10: DAVI tightens product_codes to 1..50 (owner ceiling unchanged)."""
    action = _post_action()
    args = {
        "branch": "01",
        "product_codes": [f"P{i:03d}" for i in range(count)],
    }
    if ok:
        cleaned = validate_arguments(action, args)
        assert cleaned["product_codes"] == args["product_codes"]
    else:
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, args)


def test_sec02_csv_is_not_an_array() -> None:
    """CSV strings are never a substitute for array<string>."""
    action = _post_action()
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action, {"branch": "01", "product_codes": "A,B,C"}
        )


def test_sec02_warehouse_governed_default_applied() -> None:
    """Inventory-blocks contract: omitted warehouse → governed '01'."""
    request_body = {
        "properties": {
            "branch": {"type": "string", "minLength": 2, "maxLength": 2},
            "product_codes": {"type": "array", "items": {"type": "string"}},
            "warehouse": {"type": "string"},
        },
        "required": ("branch",),
        "supported": True,
    }
    action = _post_action(
        operation_id="list_product_inventory_blocks",
        path="/products/inventory-blocks",
        request_body=request_body,
        approved_inputs=("branch", "product_codes", "warehouse"),
        constraints={
            "requireArguments": ["branch", "product_codes"],
            "argumentLimits": {
                "product_codes": {"minItems": 1, "maxItems": 50},
                "warehouse": {"default": "01"},
            },
        },
    )
    cleaned = validate_arguments(
        action, {"branch": "01", "product_codes": ["P1"]}
    )
    assert cleaned["warehouse"] == "01"


# --- executor binding -------------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, path, *, params=None, headers=None):
        self.calls.append(
            {"verb": "get", "path": path, "params": params, "headers": headers}
        )
        return self.response

    def post(self, path, *, json=None, params=None, headers=None):
        self.calls.append(
            {
                "verb": "post",
                "path": path,
                "json": json,
                "params": params,
                "headers": headers,
            }
        )
        return self.response


@pytest.fixture(autouse=True)
def _seed_post_actions():
    reset_action_index_for_tests()
    set_actions_for_tests(
        [
            _post_action(),
            _post_action(
                operation_id="list_product_inventory_blocks",
                path="/products/inventory-blocks",
                approved_inputs=("branch", "product_codes", "warehouse"),
            ),
        ]
    )
    yield
    reset_action_index_for_tests()


def test_sec02_post_executes_catalog_fixed_with_body() -> None:
    """POST-01/POST-13/POST-14: catalog-fixed path, JSON body, bound end-user auth."""
    client = _FakeClient(_FakeResponse(200, {"items": [{"product_code": "P1"}]}))
    executor = AsgiCatalogActionExecutor(
        client, authorization="Bearer end-user-token"
    )
    result = executor.execute(
        action_id="list_product_physical_locations",
        validated_arguments={"branch": "01", "product_codes": ["P1", "P2"]},
    )
    assert result.outcome == "ok"
    call = client.calls[0]
    assert call["verb"] == "post"
    assert call["path"] == "/products/physical-locations"
    assert call["json"] == {"branch": "01", "product_codes": ["P1", "P2"]}
    assert call["headers"] == {"Authorization": "Bearer end-user-token"}
    assert call["params"] in (None, {})


def test_sec02_post_without_marker_denied_at_executor() -> None:
    action = _post_action(semantic_transport=None)
    set_actions_for_tests([action])
    client = _FakeClient(_FakeResponse(200, {}))
    result = AsgiCatalogActionExecutor(
        client, authorization="Bearer t"
    ).execute(
        action_id="list_product_physical_locations",
        validated_arguments={"branch": "01"},
    )
    assert result.outcome == "error"
    assert client.calls == []


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
def test_sec02_mutating_methods_denied_at_executor(method: str) -> None:
    action = _post_action(method=method)
    set_actions_for_tests([action])
    client = _FakeClient(_FakeResponse(200, {}))
    result = AsgiCatalogActionExecutor(
        client, authorization="Bearer t"
    ).execute(
        action_id="list_product_physical_locations",
        validated_arguments={"branch": "01"},
    )
    assert result.outcome == "error"
    assert client.calls == []


def test_sec02_unsupported_body_schema_denied() -> None:
    action = _post_action(
        request_body={"properties": {}, "required": (), "supported": False}
    )
    set_actions_for_tests([action])
    client = _FakeClient(_FakeResponse(200, {}))
    result = AsgiCatalogActionExecutor(
        client, authorization="Bearer t"
    ).execute(
        action_id="list_product_physical_locations",
        validated_arguments={},
    )
    assert result.outcome == "error"
    assert client.calls == []


@pytest.mark.parametrize(
    "status,expected", [(401, "unauthorized"), (403, "forbidden")]
)
def test_sec02_post_auth_propagation(status: int, expected: str) -> None:
    """POST-11: backend 401/403 remain governed outcomes (no reconnect mapping)."""
    client = _FakeClient(_FakeResponse(status, {"detail": "nope"}))
    result = AsgiCatalogActionExecutor(
        client, authorization="Bearer end-user-token"
    ).execute(
        action_id="list_product_physical_locations",
        validated_arguments={"branch": "01", "product_codes": ["P1"]},
    )
    assert result.outcome == expected


def test_sec02_get_regression_still_works() -> None:
    """GET path unchanged: catalog-fixed GET still executes identically."""
    get_action = TechnicalAction(
        action_id="get_product_stock",
        operation_id="get_product_stock",
        method="GET",
        path="/products/{code}/stock",
        summary="fixture",
        description="fixture",
        tags=("products",),
        davi_status=STATUS_DAVI_ELIGIBLE_READ,
        approved_response_fields=("product_code",),
        approved_input_fields=("code",),
    )
    set_actions_for_tests([get_action])
    client = _FakeClient(_FakeResponse(200, {"items": []}))
    result = AsgiCatalogActionExecutor(
        client, authorization="Bearer t"
    ).execute(
        action_id="get_product_stock",
        validated_arguments={"code": "P1", "warehouse": "01"},
    )
    assert result.outcome == "ok"
    call = client.calls[0]
    assert call["verb"] == "get"
    assert call["path"] == "/products/P1/stock"
    assert call["params"] == {"warehouse": "01"}


# --- end-to-end execute (projection + actor binding) -------------------------


def _mint(action_id: str, actor_id: str = _ACTOR) -> str:
    return mint_candidate_token(
        action_id=action_id, actor_id=actor_id, secret=_SECRET, ttl_seconds=120
    )


def test_sec02_execute_drops_unapproved_owner_fields() -> None:
    """Projection parity with GET: extra owner payload fields are dropped."""

    class _Exec:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(
                outcome="ok",
                payload={
                    "items": [
                        {
                            "product_code": "P1",
                            "physical_location": "A-01",
                            "internal_debug": True,
                            "supplier_secret": "x",
                        }
                    ]
                },
            )

    with patch(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        return_value=_SECRET,
    ):
        result = execute_delpi_information(
            candidate_token=_mint("list_product_physical_locations"),
            arguments={"branch": "01", "product_codes": ["P1"]},
            actor_id=_ACTOR,
            catalog_action_executor=_Exec(),
        )
    assert result["status"] == "ok"
    item = result["data"]["items"][0]
    assert set(item) == {"product_code", "physical_location"}


def test_sec02_execute_rejects_actor_mismatch() -> None:
    """Candidate-token actor binding unchanged for POST actions."""

    class _Exec:
        def execute(self, *, action_id, validated_arguments):
            return CatalogActionExecutionResult(outcome="ok", payload={})

    with patch(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        return_value=_SECRET,
    ):
        with pytest.raises(CandidateTokenError):
            execute_delpi_information(
                candidate_token=_mint(
                    "list_product_physical_locations", actor_id="other-actor"
                ),
                arguments={"branch": "01", "product_codes": ["P1"]},
                actor_id=_ACTOR,
                catalog_action_executor=_Exec(),
            )


def test_sec02_execute_rejects_unknown_body_field_before_executor() -> None:
    """POST-09 end-to-end: unknown field never reaches the executor."""

    class _Exec:
        called = False

        def execute(self, *, action_id, validated_arguments):
            _Exec.called = True
            return CatalogActionExecutionResult(outcome="ok", payload={})

    with patch(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        return_value=_SECRET,
    ):
        with pytest.raises(GovernedExecutionError):
            execute_delpi_information(
                candidate_token=_mint("list_product_physical_locations"),
                arguments={
                    "branch": "01",
                    "product_codes": ["P1"],
                    "unknown": "x",
                },
                actor_id=_ACTOR,
                catalog_action_executor=_Exec(),
            )
    assert _Exec.called is False


# ---------------------------------------------------------------------------
# SEC-02 corrective — body-contract support must gate eligibility end to end
# ---------------------------------------------------------------------------

_POST_NO_BODY_OPENAPI: dict[str, Any] = {
    "openapi": "3.1.0",
    "paths": {
        "/products/physical-locations": {
            "post": {
                "operationId": "list_product_physical_locations",
                "summary": "Physical pickup locations in batch",
                "tags": ["products"],
            }
        }
    },
}

_POST_UNSUPPORTED_BODY_OPENAPI: dict[str, Any] = {
    "openapi": "3.1.0",
    "paths": {
        "/products/physical-locations": {
            "post": {
                "operationId": "list_product_physical_locations",
                "summary": "Physical pickup locations in batch",
                "tags": ["products"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "branch": {"type": "string"},
                                    # unsupported shape: nested object property
                                    "filter": {"type": "object"},
                                },
                                "required": ["branch"],
                            }
                        }
                    },
                },
            }
        }
    },
}


def _build_fixture_action(openapi: dict[str, Any]) -> TechnicalAction:
    actions = build_technical_actions_from_openapi(
        openapi, allowlist=_GOV_FIXTURE_ALLOWLIST
    )
    assert len(actions) == 1
    return actions[0]


def test_semantic_post_supported_body_remains_executable() -> None:
    """POST + marker + allowlist + supported requestBody → executable."""
    action = _build_fixture_action(_PHYSICAL_LOCATIONS_OPENAPI)
    assert action.davi_status == STATUS_DAVI_ELIGIBLE_READ
    assert action.executable is True


def test_semantic_post_missing_request_body_not_executable() -> None:
    """POST + marker + allowlist + NO requestBody → not eligible."""
    action = _build_fixture_action(_POST_NO_BODY_OPENAPI)
    assert action.davi_status == STATUS_NEEDS_BOUNDED_EXECUTION
    assert action.executable is False


def test_semantic_post_unsupported_request_body_not_executable() -> None:
    """POST + marker + allowlist + unsupported body shape → not eligible."""
    action = _build_fixture_action(_POST_UNSUPPORTED_BODY_OPENAPI)
    assert action.request_body is not None
    assert action.request_body.get("supported") is False
    assert action.davi_status == STATUS_NEEDS_BOUNDED_EXECUTION
    assert action.executable is False


def test_semantic_post_missing_body_not_retrieved() -> None:
    """retrieve_eligible_actions filters non-executable semantic POSTs."""
    blocked = _build_fixture_action(_POST_NO_BODY_OPENAPI)
    allowed = _build_fixture_action(_PHYSICAL_LOCATIONS_OPENAPI)
    ranked = retrieve_eligible_actions(
        "physical locations products", [blocked, allowed], top_k=5
    )
    ids = {a.action_id for a, _score in ranked}
    assert "list_product_physical_locations" in ids  # sibling stays retrievable
    assert len(ranked) == 1


def test_semantic_post_unsupported_body_not_retrieved() -> None:
    blocked = _build_fixture_action(_POST_UNSUPPORTED_BODY_OPENAPI)
    allowed = _build_fixture_action(_PHYSICAL_LOCATIONS_OPENAPI)
    ranked = retrieve_eligible_actions(
        "physical locations products", [blocked], top_k=5
    )
    assert ranked == []
    ranked2 = retrieve_eligible_actions(
        "physical locations products", [allowed], top_k=5
    )
    assert [a.action_id for a, _ in ranked2] == ["list_product_physical_locations"]


def test_semantic_post_missing_body_not_discovered(monkeypatch) -> None:
    """discover must not emit a candidate_token for a body-missing POST."""
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    blocked = _build_fixture_action(_POST_NO_BODY_OPENAPI)
    set_actions_for_tests([blocked])
    result = discover_delpi_information(
        query="physical locations products", top_k=5, actor_id=_ACTOR
    )
    assert result["eligible_action_count"] == 0
    assert result["candidate_count"] == 0
    assert result["candidates"] == []


def test_semantic_post_unsupported_body_not_discovered(monkeypatch) -> None:
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    blocked = _build_fixture_action(_POST_UNSUPPORTED_BODY_OPENAPI)
    set_actions_for_tests([blocked])
    result = discover_delpi_information(
        query="physical locations products", top_k=5, actor_id=_ACTOR
    )
    assert result["eligible_action_count"] == 0
    assert result["candidate_count"] == 0
    assert result["candidates"] == []


def test_baseline_semantic_post_without_body_is_not_executable() -> None:
    """Baseline fallback carries no requestBody: governed POST must stay closed."""
    baseline = {
        "operations": [
            {
                "method": "post",
                "path": "/products/physical-locations",
                "operationId": "list_product_physical_locations",
                "summary": "Physical pickup locations in batch",
                "tags": ["products"],
            }
        ]
    }
    actions = build_technical_actions_from_baseline(
        baseline, allowlist=_GOV_FIXTURE_ALLOWLIST
    )
    assert len(actions) == 1
    action = actions[0]
    assert action.semantic_transport == SEMANTIC_TRANSPORT_READ_POST
    assert action.request_body is None
    assert action.davi_status == STATUS_NEEDS_BOUNDED_EXECUTION
    assert action.executable is False
    ranked = retrieve_eligible_actions(
        "physical locations products", actions, top_k=5
    )
    assert ranked == []
