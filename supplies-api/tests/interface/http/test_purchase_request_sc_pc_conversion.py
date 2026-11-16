"""GLPI #635: BFF must authorize scope before forwarding to TOTVS."""

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def identity():
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br", name="Buyer",
    )


def user(permissions):
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br", name="Buyer",
        permissions=set(permissions), is_superadmin=False,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_conversion_rejects_missing_access_and_unit(mock_resolve, mock_validate):
    mock_validate.return_value = identity()
    mock_resolve.return_value = user(set())
    gateway = MagicMock()
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        client = create_app().test_client()
        assert client.get("/purchase-requests/sc-pc-conversion?branch=01",
                          headers={"Authorization": "Bearer tok"}).status_code == 403
        mock_resolve.return_value = user({"supplies.access"})
        assert client.get("/purchase-requests/sc-pc-conversion",
                          headers={"Authorization": "Bearer tok"}).status_code == 403
        assert client.get("/purchase-requests/sc-pc-conversion?branch=03",
                          headers={"Authorization": "Bearer tok"}).status_code == 403
        assert client.get("/purchase-requests/sc-pc-conversion?branch=01&other=x",
                          headers={"Authorization": "Bearer tok"}).status_code == 422
    gateway.get.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_conversion_forwards_branch_scope_and_validates_provenance(mock_resolve, mock_validate):
    mock_validate.return_value = identity()
    mock_resolve.return_value = user({"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = {"success": True, "data": {
        "source": "SC1010+SCR010+SC7010",
        "scope": "confirmed_release_to_first_order",
        "period_anchor": "final_approval_date",
        "summary": {"approved_requests": 1, "converted_requests": 1, "avg_days": 2},
        "branch_breakdown": {"01": {"converted_requests": 1}},
        "items": [],
    }}
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/sc-pc-conversion?branch=01&date_from=2026-10-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["summary"]["avg_days"] == 2
    args = gateway.get.call_args
    assert args.args[0] == "/supplies/purchase-requests/sc-pc-conversion"
    assert args.kwargs["access_token"] == "token"
    assert ("branch", "01") in args.kwargs["params"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user")
def test_conversion_fails_closed_on_invalid_source_or_upstream(mock_resolve, mock_validate):
    mock_validate.return_value = identity()
    mock_resolve.return_value = user({"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = {"success": True, "data": {"summary": {}, "items": []}}
    with patch("app.interfaces.http.routes.purchase_requests_routes._APPROVAL_DELPI", gateway):
        response = create_app().test_client().get(
            "/purchase-requests/sc-pc-conversion?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        assert response.status_code == 502
        gateway.get.side_effect = DelpiApiGatewayError("down", status_code=503)
        response = create_app().test_client().get(
            "/purchase-requests/sc-pc-conversion?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        assert response.status_code == 503
        assert response.get_json()["code"] == "totvs_unavailable"

        gateway.get.side_effect = DelpiApiGatewayError(
            "api-delpi timeout", status_code=504, code="upstream_timeout",
        )
        response = create_app().test_client().get(
            "/purchase-requests/sc-pc-conversion?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        assert response.status_code == 504
        assert response.get_json()["code"] == "upstream_timeout"
        assert "Protheus" in response.get_json()["detail"]

        gateway.get.side_effect = DelpiApiGatewayError(
            "producer_error", status_code=500,
        )
        response = create_app().test_client().get(
            "/purchase-requests/sc-pc-conversion?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
        assert response.status_code == 502
        assert response.get_json()["code"] == "upstream_failure"
