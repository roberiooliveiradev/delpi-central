from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser


def _user(*, permissions: set[str]) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=False,
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
def test_export_positive_with_export_capability(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.purchase-requests.access",
            "supplies.purchase-requests.export",
            "supplies.unit.filial-01",
        }
    )
    gateway = MagicMock()
    gateway.list_purchase_requests.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "branch": "01",
                    "request_number": "100",
                    "request_item": "0001",
                    "product_code": "P1",
                    "product_description": "Parafuso",
                    "requester": {"name": "Ana"},
                    "cost_center_code": "CC01",
                    "request_issue_date": "2026-09-01",
                    "derived": {"overall_stage": "awaiting_order"},
                    "approval": {"status": "approved"},
                }
            ],
            "total": 1,
        },
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/export?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert "text/csv" in (response.mimetype or "")
    body = response.get_data(as_text=True)
    assert "request_number" in body
    assert "100" in body


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_export_negative_without_export_capability(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.purchase-requests.access",
            "supplies.unit.filial-01",
        }
    )
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests/export?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_export_sibling_forbidden_wrong_unit(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.purchase-requests.access",
            "supplies.purchase-requests.export",
            "supplies.unit.filial-01",
        }
    )
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests/export?branch=02",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403
