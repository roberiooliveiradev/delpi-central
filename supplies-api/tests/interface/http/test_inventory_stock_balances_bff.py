"""HTTP BFF — inventory stock balances (E10.S2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.exceptions import CoreApiUnavailableError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _summary_envelope(*, branches: list[str] | None = None) -> dict:
    return {
        "success": True,
        "data": {
            "summary": {
                "branch": ",".join(branches or ["01"]),
                "warehouse": "all",
                "product_count": 10,
                "total_quantity": 100.0,
                "total_stock_value": 1000.0,
                "total_stock_value_vatu1": 1000.0,
                "warehouse_count": 2,
                "valuation": "qatu_times_cm1_same_local",
            },
            "by_warehouse": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "warehouse_label": "Almoxarifado",
                    "product_count": 4,
                    "total_quantity": 40.0,
                    "total_stock_value": 400.0,
                    "total_stock_value_vatu1": 400.0,
                },
                {
                    "branch": "02",
                    "warehouse": "01",
                    "warehouse_label": None,
                    "product_count": 6,
                    "total_quantity": 60.0,
                    "total_stock_value": 600.0,
                    "total_stock_value_vatu1": 600.0,
                },
            ],
        },
    }


def _items_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "product_code": "10070821",
                    "description": "CABO PP",
                    "unit_of_measure": "PC",
                    "branch": "01",
                    "warehouse": "01",
                    "warehouse_label": "Almoxarifado",
                    "quantity": 10.0,
                    "unit_cost": 1.5,
                    "stock_value": 15.0,
                },
                {
                    "product_code": "99999999",
                    "description": "SEM UM",
                    "unit_of_measure": None,
                    "branch": "01",
                    "warehouse": "03",
                    "warehouse_label": None,
                    "quantity": 0.0,
                    "unit_cost": 2.0,
                    "stock_value": 0.0,
                },
                {
                    "product_code": "MOD21101",
                    "description": "NEGATIVO",
                    "unit_of_measure": "HR",
                    "branch": "02",
                    "warehouse": "",
                    "warehouse_label": None,
                    "quantity": -5.0,
                    "unit_cost": 1.0,
                    "stock_value": -5.0,
                },
            ],
            "page": 1,
            "page_size": 50,
            "total": 3,
            "total_pages": 1,
            "sort": "stock_value_desc",
            "pagination": {
                "page": 1,
                "page_size": 50,
                "total": 3,
                "total_pages": 1,
                "is_complete": True,
            },
        },
    }


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.manage"})
    client = create_app().test_client()
    response = client.get(
        "/inventory/stock-balances/summary",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_core_unavailable_fail_closed(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core down")
    client = create_app().test_client()
    response = client.get(
        "/inventory/stock-balances/summary",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 503
    assert response.get_json()["detail"] == "Core down"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_empty_branch_is_todas_one_upstream_call(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _summary_envelope(branches=["01", "02"])
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/inventory/stock-balances/summary",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["applied_filters"]["branches"] == ["01", "02"]
    assert body["summary"]["product_count"] == 10
    assert body["by_warehouse"][1]["warehouse_label"] is None
    assert gateway.get.call_count == 1
    assert gateway.get.call_args.args[0] == "/supplies/stock-balances/summary"
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == ["01", "02"]
    assert params["only_positive"] == "false"
    assert "all" not in str(params.get("branch"))


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_branch_all_normalizes_to_01_02(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _summary_envelope(branches=["01", "02"])
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/inventory/stock-balances/summary?branch=all",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == ["01", "02"]
    assert params["only_positive"] == "false"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_single_and_reverse_order(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _summary_envelope(branches=["01"])
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        r01 = client.get(
            "/inventory/stock-balances/summary?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        r02 = client.get(
            "/inventory/stock-balances/summary?branch=02",
            headers={"Authorization": "Bearer tok"},
        )
        r_rev = client.get(
            "/inventory/stock-balances/summary?branch=02&branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        r_dup = client.get(
            "/inventory/stock-balances/summary?branch=01&branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert r01.status_code == 200
    assert r02.status_code == 200
    assert r_rev.status_code == 200
    assert r_dup.status_code == 200
    calls = [c.kwargs["params"]["branch"] for c in gateway.get.call_args_list]
    assert calls[0] == ["01"]
    assert calls[1] == ["02"]
    assert calls[2] == ["01", "02"]
    assert calls[3] == ["01"]
    assert all(c.kwargs["params"]["only_positive"] == "false" for c in gateway.get.call_args_list)


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_invalid_branch_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    for query in ("branch=03", "branch=99", "branch=*", "branch=04"):
        response = client.get(
            f"/inventory/stock-balances/summary?{query}",
            headers={"Authorization": "Bearer tok"},
        )
        assert response.status_code == 422, query


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_items_preserves_um_zero_negative_and_null_label(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _items_envelope()
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/inventory/stock-balances/items?branch=01&branch=02&page=1&page_size=50",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    items = body["items"]
    assert items[0]["unit_of_measure"] == "PC"
    assert items[1]["unit_of_measure"] is None
    assert items[1]["warehouse_label"] is None
    assert items[1]["quantity"] == 0.0
    assert items[2]["quantity"] == -5.0
    assert items[2]["warehouse"] == ""
    assert body["applied_filters"]["branches"] == ["01", "02"]
    params = gateway.get.call_args.kwargs["params"]
    assert params["only_positive"] == "false"
    assert params["branch"] == ["01", "02"]
    assert params["page"] == 1
    assert params["page_size"] == 50
    # BFF must not recompute stock_value
    assert items[0]["stock_value"] == 15.0


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_items_pagination_and_sort_validation(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _items_envelope()
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        ok = client.get(
            "/inventory/stock-balances/items?branch=01&sort=quantity_asc&page_size=500",
            headers={"Authorization": "Bearer tok"},
        )
        bad_sort = client.get(
            "/inventory/stock-balances/items?branch=01&sort=hack",
            headers={"Authorization": "Bearer tok"},
        )
        bad_size = client.get(
            "/inventory/stock-balances/items?branch=01&page_size=501",
            headers={"Authorization": "Bearer tok"},
        )
        bad_page = client.get(
            "/inventory/stock-balances/items?branch=01&page=0",
            headers={"Authorization": "Bearer tok"},
        )
    assert ok.status_code == 200
    assert gateway.get.call_args.kwargs["params"]["sort"] == "quantity_asc"
    assert gateway.get.call_args.kwargs["params"]["page_size"] == 500
    assert bad_sort.status_code == 422
    assert bad_size.status_code == 422
    assert bad_page.status_code == 422


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_items_warehouse_passthrough(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _items_envelope()
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/inventory/stock-balances/items?branch=01&warehouse=25",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert gateway.get.call_args.kwargs["params"]["warehouse"] == "25"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_upstream_error_mapping(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    cases = [
        (401, 401, "unauthorized"),
        (403, 403, "forbidden"),
        (422, 422, "upstream_client_error"),
        (500, 502, "bad_gateway"),
    ]
    for upstream, expected, code in cases:
        gateway = MagicMock()
        gateway.get.side_effect = DelpiApiGatewayError(
            "api-delpi client error", status_code=upstream
        )
        with patch(
            "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
            return_value=gateway,
        ):
            response = client.get(
                "/inventory/stock-balances/summary?branch=01",
                headers={"Authorization": "Bearer tok"},
            )
        assert response.status_code == expected
        assert response.get_json()["code"] == code

    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        response = client.get(
            "/inventory/stock-balances/summary?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"


def test_inventory_routes_registered():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/inventory/stock-balances/summary" in rules
    assert "/inventory/stock-balances/items" in rules
