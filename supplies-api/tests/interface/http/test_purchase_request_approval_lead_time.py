"""HD #1004: authenticated Supplies BFF is the only browser path to SCR history."""
from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _identity():
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _user(permissions):
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=set(permissions),
        is_superadmin=False,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_scr_lead_time_requires_portal_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(set())
    gateway = MagicMock()
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/approval-lead-time?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_scr_lead_time_rejects_missing_unit_and_extra_filters(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user({"supplies.access"})
    gateway = MagicMock()
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        client = create_app().test_client()
        assert client.get(
            "/purchase-requests/approval-lead-time",
            headers={"Authorization": "Bearer tok"},
        ).status_code == 403
        assert client.get(
            "/purchase-requests/approval-lead-time?branch=01&unexpected=1",
            headers={"Authorization": "Bearer tok"},
        ).status_code == 422
        assert client.get(
            "/purchase-requests/approval-lead-time?branch=03",
            headers={"Authorization": "Bearer tok"},
        ).status_code == 403
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_scr_lead_time_forwards_only_authorized_scope(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user({"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = {
        "success": True,
        "data": {
            "source": "SCR010",
            "scope": "confirmed_history_only",
            "summary": {"total_requests": 1, "avg_lead_days": 10},
            "items": [{"branch": "01", "request_number": "171945", "lead_days": 10}],
            "total": 1, "page": 1, "page_size": 25, "total_pages": 1,
        },
    }
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/approval-lead-time?branch=01&date_from=2026-01-01&date_to=2026-11-12",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["source"] == "SCR010"
    kwargs = gateway.get.call_args.kwargs
    assert kwargs["access_token"] == "token"
    assert ("branch", "01") in kwargs["params"]
    assert ("date_from", "2026-01-01") in kwargs["params"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_scr_lead_time_fails_closed_on_invalid_upstream(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user({"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = {"success": True, "data": {"items": [], "summary": {}}}
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/approval-lead-time?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502

    gateway.get.side_effect = DelpiApiGatewayError("down", status_code=503)
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/approval-lead-time?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
