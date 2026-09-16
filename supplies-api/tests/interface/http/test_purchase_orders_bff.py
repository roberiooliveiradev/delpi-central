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


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_positive_requires_operations_and_unit(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.get.return_value = {
        "success": True,
        "data": {
            "items": [{"order_number": "000123", "delivery_status": "on_time"}],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "summary": {
                "total_lines": 4,
                "total_open_value": 1200.5,
                "late_lines": 1,
                "on_time_lines": 2,
                "no_date_lines": 1,
            },
        },
    }
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders?branch=01&late_only=true",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["order_number"] == "000123"
    assert body["summary"]["total_lines"] == 4
    assert body["summary"]["late_lines"] == 1
    assert body["summary"]["total_open_value"] == 1200.5
    assert body["summary"]["on_time_lines"] == 2
    assert body["summary"]["no_date_lines"] == 1
    gateway.get.assert_called_once()
    called_params = gateway.get.call_args.kwargs["params"]
    assert called_params["branch"] == "01"
    assert called_params["late_only"] == "true"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_negative_forbidden_without_unit(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.operations.access"})
    client = create_app().test_client()
    response = client.get(
        "/purchase-orders?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_sibling_forbidden_without_operations(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.unit.filial-01", "supplies.portal.access"}
    )
    gateway = MagicMock()
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_summary_pass_through_does_not_recalculate(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.get.return_value = {
        "success": True,
        "data": {
            "items": [{"order_number": "1"}, {"order_number": "2"}],
            "page": 1,
            "page_size": 50,
            "total": 2,
            "total_pages": 1,
            "summary": {
                "total_lines": 10,
                "total_open_value": 999.0,
                "late_lines": 3,
                "on_time_lines": 5,
                "no_date_lines": 2,
            },
        },
    }
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    body = response.get_json()
    assert response.status_code == 200
    # Pass-through: counters come from upstream summary, not items.length.
    assert body["summary"]["total_lines"] == 10
    assert body["summary"]["late_lines"] == 3
    assert len(body["items"]) == 2
    assert body["summary"]["total_lines"] != len(body["items"])


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_maps_upstream_5xx(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error",
        status_code=503,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_maps_upstream_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    assert response.get_json()["code"] == "forbidden"


_OPS_UNIT_01 = {
    "supplies.operations.access",
    "supplies.unit.filial-01",
}


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_positive_item_level_supplier(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.return_value = {
        "success": True,
        "data": {
            "branch": "01",
            "order_number": "000123",
            "items": [
                {
                    "order_item": "0001",
                    "supplier_code": "A001",
                    "source_request_number": "164708",
                    "receipts": [{"invoice_number": "NF1", "quantity": 2}],
                }
            ],
        },
    }
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["branch"] == "01"
    assert body["order_number"] == "000123"
    assert "supplier" not in body
    assert "supplier_code" not in body
    assert body["items"][0]["supplier_code"] == "A001"
    assert body["items"][0]["receipts"][0]["invoice_number"] == "NF1"
    gateway.get.assert_called_once()
    assert gateway.get.call_args.args[0] == "/supplies/purchase-orders/01/000123"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_negative_forbidden_without_operations(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.unit.filial-01", "supplies.portal.access"}
    )
    gateway = MagicMock()
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_negative_cross_unit_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/02/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_maps_upstream_not_found(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=404,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/999999",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_maps_upstream_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    assert response.get_json()["code"] == "forbidden"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_maps_upstream_timeout_to_502(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_maps_upstream_5xx_to_502(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error",
        status_code=503,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_maps_upstream_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=_OPS_UNIT_01)
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=422,
    )
    with patch(
        "app.interfaces.http.routes.purchase_orders_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-orders/01/000123",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422
    assert response.get_json()["code"] == "upstream_client_error"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_core_unavailable_returns_503(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core API request failed")
    client = create_app().test_client()
    response = client.get(
        "/purchase-orders/01/000123",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 503
