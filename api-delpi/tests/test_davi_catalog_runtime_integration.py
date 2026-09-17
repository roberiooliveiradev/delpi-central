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
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase",
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


def _pricing_payload() -> dict[str, Any]:
    return {
        "product": {"code": "10080055", "description": "PA", "unit": "UN"},
        "prices": [
            {
                "table_code": "001",
                "table_description": "Padrao",
                "sale_price": 12.5,
                "currency": "1",
                "lot_quantity": 1.0,
                "valid_from": "20260101",
                "active": "S",
                "max_price": 99.0,
                "discount_value": 1.5,
                "discount_percent": 10.0,
                "state": "SP",
                "operation_type": "V",
                "internal_debug": True,
            }
        ],
        "standard_cost": 0.5,
    }


def _history_payload() -> dict[str, Any]:
    return {
        "product": {
            "product_code": "10080055",
            "description": "MP",
            "product_type": "MP",
            "unit": "KG",
            "registered_last_purchase_price": 0.5,
            "standard_cost": 0.02,
        },
        "start_date": "20250917",
        "date_end_exclusive": "20260918",
        "branch": "all",
        "items": [
            {
                "issue_date": "20260901",
                "invoice_number": "000200",
                "supplier_code": "S2",
                "supplier_name": "Beta",
                "quantity": 5,
                "unit_price": 0.20,
                "total_value": 1.0,
                "icms_rate": 12.0,
                "previous_unit_price": 0.10,
                "variation_percent": 100.0,
                "entry_date": "20260902",
                "invoice_series": "1",
                "supplier_store": "01",
                "icms_value": 0.12,
                "purchase_order": "PC9",
                "supplier_tax_id": "12345678000199",
            },
            {
                "issue_date": "20260801",
                "invoice_number": "000100",
                "supplier_code": "S1",
                "supplier_name": "Alfa",
                "quantity": 2,
                "unit_price": 0.10,
                "total_value": 0.2,
                "icms_rate": 12.0,
                "previous_unit_price": None,
                "variation_percent": None,
            },
        ],
        "summary": {
            "total_purchases": 2,
            "min_unit_price": 0.10,
            "max_unit_price": 0.20,
            "avg_unit_price": 0.15,
            "last_variation_percent": 100.0,
        },
    }


def _last_purchase_payload() -> dict[str, Any]:
    return {
        "product": {
            "product_code": "10080055",
            "description": "MP",
            "product_type": "MP",
            "unit": "KG",
            "standard_cost": 0.02,
        },
        "last_purchase": {
            "branch": "01",
            "invoice_number": "000123",
            "issue_date": "20200407",
            "supplier_code": "000002",
            "supplier_name": "TE",
            "quantity": 10,
            "unit_price": 0.089,
            "total_value": 0.89,
            "icms_rate": 12.0,
            "purchase_order": "PC1",
            "supplier_tax_id": "12345678000199",
            "supplier_state": "SP",
            "supplier_part_number": "PN",
            "invoice_series": "1",
            "entry_date": "20200408",
            "supplier_store": "01",
            "icms_value": 0.1,
        },
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

    pricing_uc = MagicMock()
    pricing_uc.execute.return_value = _pricing_payload()

    history_uc = MagicMock()
    history_uc.execute.return_value = _history_payload()

    last_purchase_uc = MagicMock()
    last_purchase_uc.execute.return_value = _last_purchase_payload()

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
            patch.object(
                product_routes,
                "build_get_product_pricing",
                return_value=pricing_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_get_product_purchase_price_history_use_case",
                return_value=history_uc,
            )
        )
        stack.enter_context(
            patch.object(
                product_routes,
                "build_get_product_last_purchase_use_case",
                return_value=last_purchase_uc,
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


def test_wave2_pricing_history_last_purchase_wired_projection(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=True):
        pricing = _execute("get_product_pricing", {"code": "10080055"})
        history = _execute(
            "get_product_purchase_price_history", {"code": "10080055"}
        )
        last = _execute("get_product_last_purchase", {"code": "10080055"})
    dumped_p = json.dumps(pricing.get("data") or {}, default=str)
    assert pricing["status"] == "ok"
    assert pricing["data"]["prices"][0]["sale_price"] == 12.5
    assert pricing["data"]["prices"][0]["currency"] == "1"
    for sibling in (
        "max_price",
        "discount_value",
        "discount_percent",
        "state",
        "operation_type",
        "standard_cost",
        "internal_debug",
    ):
        assert sibling not in dumped_p

    dumped_h = json.dumps(history.get("data") or {}, default=str)
    assert history["status"] == "ok"
    items = history["data"]["items"]
    assert [row["invoice_number"] for row in items] == ["000200", "000100"]
    assert history["data"]["summary"]["total_purchases"] == 2
    for sibling in (
        "registered_last_purchase_price",
        "standard_cost",
        "entry_date",
        "invoice_series",
        "supplier_store",
        "icms_value",
        "purchase_order",
        "supplier_tax_id",
        "12345678000199",
    ):
        assert sibling not in dumped_h

    dumped_l = json.dumps(last.get("data") or {}, default=str)
    assert last["status"] == "ok"
    assert last["data"]["last_purchase"]["invoice_number"] == "000123"
    assert last["data"]["last_purchase"]["unit_price"] == 0.089
    for sibling in (
        "supplier_tax_id",
        "12345678000199",
        "supplier_state",
        "supplier_part_number",
        "invoice_series",
        "entry_date",
        "supplier_store",
        "icms_value",
        "standard_cost",
    ):
        assert sibling not in dumped_l


def test_wave2_backend_403_maps_to_forbidden(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    monkeypatch.setenv(
        "KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi"
    )
    with _auth_and_domain_fakes(allowed=False):
        for action_id in (
            "get_product_pricing",
            "get_product_purchase_price_history",
            "get_product_last_purchase",
        ):
            with pytest.raises(PermissionError, match="Forbidden"):
                _execute(action_id, {"code": "10080055"})


def test_eligible_set_is_thirteen():
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
        "get_product_pricing",
        "get_product_purchase_price_history",
        "get_product_last_purchase",
    }


def test_unknown_argument_still_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", _SECRET)
    with _auth_and_domain_fakes(allowed=True):
        with pytest.raises(GovernedExecutionError):
            _execute(
                "get_product_stock",
                {"code": "10080055", "sql": "select 1"},
            )
