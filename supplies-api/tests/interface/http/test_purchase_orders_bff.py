from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
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
