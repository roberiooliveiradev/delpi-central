"""In-process runtime integration: DAVI catalog actions via real composition.

Proves execute_delpi_information_wired → InProcessAsgiClient → canonical routes
without mocking CatalogActionExecutor. DB/use-case boundaries may be faked.
"""

from __future__ import annotations

import json
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    mint_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.composition.davi_dynamic_read_composer import execute_delpi_information_wired
from app.interface.mcp.server import create_mcp_server
import app.interface.http.routes.product_routes as product_routes

_BASELINE = (
    Path(__file__).resolve().parents[1] / "app" / "content" / "openapi_baseline.json"
)
_ACTOR = "11111111-1111-4111-8111-111111111111"
_SECRET = "test-secret-davi-catalog-runtime"
_CLAIMS = {
    "sub": _ACTOR,
    "email": "davi-runtime@example.com",
    "aud": "delpi-central",
    "name": "DAVI Runtime",
}

_CATALOG_ACTIONS = (
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
)


class _Paged:
    def __init__(self, items: list[dict[str, Any]]):
        self._items = items

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self._items,
            "page": 1,
            "page_size": 50,
            "total": len(self._items),
            "total_pages": 1,
        }


def _stock_payload() -> dict[str, Any]:
    return {
        "items": [
            {
                "product_code": "10080055",
                "branch": "01",
                "warehouse": "01",
                "current_quantity": 10.0,
                "committed_quantity": 1.0,
                "reserved_quantity": 1.0,
                "available_quantity": 8.0,
                "physical_location": None,
                "default_warehouse": None,
                "cost_center": None,
                "warehouse_section": None,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }


def _structure_payload() -> dict[str, Any]:
    return {
        "root": {
            "code": "10080055",
            "description": "PA root",
            "type": "PA",
            "unit": "UN",
            "quantity": 1.0,
            "components": [
                {
                    "code": "MP-1",
                    "description": "Material",
                    "type": "MP",
                    "unit": "KG",
                    "quantity": 2.0,
                    "components": [],
                }
            ],
        },
        "items": [],
    }


def _production_payload() -> dict[str, Any]:
    return {
        "product": {
            "product_code": "10080055",
            "description": "PA",
            "product_type": "PA",
            "unit": "UN",
            "group_code": "G1",
        },
        "reference_date": "2026-01-15",
        "items": [
            {
                "level": 0,
                "product_code": "10080055",
                "branch": "01",
                "production_order": "OP-1",
                "order_number": "1",
                "order_status": "A",
                "order_quantity": 10.0,
                "produced_quantity_sc2": 5.0,
                "planned_start_date": "2026-01-01",
                "planned_end_date": "2026-01-10",
                "actual_end_date": None,
            }
        ],
        "summary": {
            "total_pa_orders": 1,
            "total_pi_orders": 0,
            "pa_production_started": True,
            "pi_production_started": False,
        },
    }


@pytest.fixture(autouse=True)
def _seed_eligible_actions():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    actions = build_technical_actions_from_baseline(
        json.loads(_BASELINE.read_text(encoding="utf-8")),
        allowlist=load_external_read_allowlist(),
    )
    set_actions_for_tests(actions)
    yield
    reset_action_index_for_tests()


@contextmanager
def _auth_and_domain_fakes(*, allowed: bool = True) -> Iterator[None]:
    user = MagicMock()
    user.id = _ACTOR
    user.email = "davi-runtime@example.com"
    user.is_superadmin = allowed
    user.permissions = ["api-delpi.access"] if allowed else []
    user.rbac_unavailable = False

    stock_uc = MagicMock()
    stock_uc.execute.return_value = _stock_payload()

    suppliers_uc = MagicMock()
    suppliers_uc.execute.return_value = _Paged(
        [
            {
                "product_code": "10080055",
                "supplier_code": "S1",
                "supplier_store": "01",
                "supplier_name": "Fornecedor",
                "supplier_part_number": "PN",
                "unit": "UN",
                "registered_lead_time_days": 7,
            }
        ]
    )

    customers_uc = MagicMock()
    customers_uc.execute.return_value = _Paged(
        [
            {
                "product_code": "10080055",
                "customer_code": "C1",
                "store": "01",
                "customer_name": "Cliente",
                "blocked": False,
                "customer_product_code": "CP",
                "unit": "UN",
                "total_quantity": 3.0,
            }
        ]
    )

    purchases_uc = MagicMock()
    purchases_uc.execute.return_value = {
        "items": [
            {
                "order_number": "PC-1",
                "branch": "01",
                "issue_date": "2026-01-02",
                "supplier_code": "S1",
                "store": "01",
                "supplier_name": "Fornecedor",
                "product_code": "10080055",
                "ordered_quantity": 4.0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }

    structure_uc = MagicMock()
    structure_uc.execute.return_value = _structure_payload()

    production_uc = MagicMock()
    production_uc.execute.return_value = _production_payload()

    search_uc = MagicMock()

    class _SearchPage:
        def to_dict(self) -> dict[str, Any]:
            return {
                "items": [
                    {
                        "code": "10080055",
                        "description": "Produto",
                        "group_code": "G1",
                        "customer_reference": "SECRET",
                    }
                ],
                "page": 1,
                "page_size": 50,
                "total": 1,
                "total_pages": 1,
            }

    search_uc.execute.return_value = _SearchPage()

    async def _rbac(_token: str) -> dict[str, Any]:
        return {
            "id": _ACTOR,
            "email": "davi-runtime@example.com",
            "name": "DAVI Runtime",
            "roles": [],
            "groups": [],
            "permissions": ["api-delpi.access"] if allowed else [],
            "is_superadmin": allowed,
            "rbac_unavailable": False,
        }

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                product_routes,
                "build_list_product_stock_use_case",
                return_value=stock_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_list_product_suppliers_use_case",
                return_value=suppliers_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_list_customers_use_case",
                return_value=customers_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_list_product_purchases",
                return_value=purchases_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_list_structure_use_case",
                return_value=structure_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_get_product_production_status_use_case",
                return_value=production_uc,
            )
        )
        stack.enter_context(
            patch(
                "app.composition.product_composer.build_search_products_use_case",
                return_value=search_uc,
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
        stack.enter_context(
            patch(
                "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
                lambda: _SECRET,
            )
        )
        stack.enter_context(
            patch(
                "app.application.external_capabilities.product_search_service.require_product_search_access",
                lambda: None,
            )
        )
        yield


def _mint(action_id: str) -> str:
    return mint_candidate_token(
        action_id=action_id,
        actor_id=_ACTOR,
        secret=_SECRET,
        ttl_seconds=120,
    )


def _execute(action_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return execute_delpi_information_wired(
        candidate_token=_mint(action_id),
        arguments=arguments,
        actor_id=_ACTOR,
        authorization="Bearer end-user-token",
    )


@pytest.mark.parametrize("action_id", _CATALOG_ACTIONS)
def test_catalog_action_wired_execute_pass(action_id: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=True):
        result = _execute(action_id, {"code": "10080055"})
    assert result["status"] == "ok"
    assert result["action_id"] == action_id
    assert result["projection"] == "approved_fields"
    assert result.get("data") is not None


def test_stock_projection_and_branch_filter(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=True):
        result = _execute(
            "get_product_stock",
            {"code": "10080055", "branch": "01"},
        )
    items = (result.get("data") or {}).get("items") or []
    assert items == [
        {
            "product_code": "10080055",
            "branch": "01",
            "warehouse": "01",
            "current_quantity": 10.0,
            "available_quantity": 8.0,
        }
    ]


def test_structure_nested_projection(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=True):
        result = _execute("get_product_structure", {"code": "10080055"})
    root = (result.get("data") or {}).get("root") or {}
    assert root["code"] == "10080055"
    assert root["components"][0]["code"] == "MP-1"
    assert "secret" not in root


def test_nested_under_running_app_lifespan(monkeypatch: pytest.MonkeyPatch):
    """Regression for live Internal error: nested lifespan / MCP session manager."""
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=True):
        from app.main import app

        @app.get("/__davi_catalog_runtime_probe")
        def _probe() -> dict[str, Any]:
            out = _execute(
                "get_product_stock",
                {"code": "10080055", "branch": "02"},
            )
            return {
                "status": out["status"],
                "action_id": out["action_id"],
                "items": (out.get("data") or {}).get("items"),
            }

        with TestClient(app) as client:
            response = client.get(
                "/__davi_catalog_runtime_probe",
                headers={"Authorization": "Bearer outer"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["action_id"] == "get_product_stock"
    assert body["items"][0]["branch"] == "01"


def test_backend_403_maps_to_forbidden(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=False):
        with pytest.raises(PermissionError, match="Forbidden"):
            _execute("get_product_stock", {"code": "10080055"})


def test_search_products_discover_execute_still_pass(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: _SECRET,
    )
    from app.application.external_capabilities.dynamic_information.discover_service import (
        discover_delpi_information,
    )

    with _auth_and_domain_fakes(allowed=True):
        discovered = discover_delpi_information(
            query="estoque do produto 10080055",
            top_k=5,
            actor_id=_ACTOR,
        )
        assert discovered["candidate_count"] >= 1
        assert discovered["candidates"][0]["action_id"] == "get_product_stock"
        token = discovered["candidates"][0]["candidate_token"]
        executed = execute_delpi_information_wired(
            candidate_token=token,
            arguments={"code": "10080055"},
            actor_id=_ACTOR,
            authorization="Bearer end-user-token",
        )
        assert executed["status"] == "ok"
        assert executed["action_id"] == "get_product_stock"

        search_token = mint_candidate_token(
            action_id="search_products",
            actor_id=_ACTOR,
            secret=_SECRET,
            ttl_seconds=120,
        )
        search = execute_delpi_information_wired(
            candidate_token=search_token,
            arguments={"code": "10080055"},
            actor_id=_ACTOR,
            authorization="Bearer end-user-token",
        )
        assert search["status"] == "ok"
        assert search["action_id"] == "search_products"


def test_mcp_still_exposes_exactly_three_tools():
    mcp = create_mcp_server()
    tools = {t.name for t in mcp._tool_manager.list_tools()}
    assert tools == {
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    }


def test_eligible_set_is_ten():
    ids = load_allowlist_operation_ids(load_external_read_allowlist())
    assert ids == {
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
    }


def test_unknown_argument_still_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    with _auth_and_domain_fakes(allowed=True):
        with pytest.raises(GovernedExecutionError):
            _execute(
                "get_product_stock",
                {"code": "10080055", "sql": "select 1"},
            )
