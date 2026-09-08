from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser


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
def test_list_positive_requires_access_and_unit(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.purchase-requests.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.list_purchase_requests.return_value = {
        "success": True,
        "data": {"items": [{"request_number": "100"}], "total": 1},
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["total"] == 1
    gateway.list_purchase_requests.assert_called_once()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_negative_forbidden_without_unit(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.purchase-requests.access"})
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_sibling_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.unit.filial-01", "supplies.portal.access"}
    )
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_detail_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.purchase-requests.access",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.get_purchase_request.return_value = {
        "success": True,
        "data": {"header": {"request_number": "100"}, "lines": []},
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/01/100",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["header"]["request_number"] == "100"
