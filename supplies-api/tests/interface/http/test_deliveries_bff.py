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


def _panel_payload(*, branch: str, items: list[dict], total: int | None = None) -> dict:
    total_value = total if total is not None else len(items)
    return {
        "success": True,
        "data": {
            "branch": branch,
            "product_type": "MP",
            "summary": {
                "total_lines": total_value,
                "on_time_lines": 0,
                "late_lines": total_value,
                "purchase_order_otd_pct": 0.0,
                "late_percentage": 100.0,
            },
            "lines": {
                "items": items,
                "page": 1,
                "page_size": 20,
                "total": total_value,
                "total_pages": 1 if total_value else 0,
            },
        },
    }


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_positive_single_branch(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _panel_payload(
        branch="01",
        items=[
            {
                "branch": "01",
                "order_number": "000100",
                "order_item": "0001",
                "status": "late",
                "days_diff": -2,
                "expected_delivery_date": "2026-09-01",
                "receipt_entry_date": "2026-09-03",
            }
        ],
    )
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/deliveries/late?branch=01&status=late&start_date=2026-09-01&end_date=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["branch"] == "01"
    assert body["items"][0]["order_number"] == "000100"
    assert body["applied_filters"]["branches"] == ["01"]
    assert body["applied_filters"]["status"] == "late"
    assert gateway.get.call_count == 1
    path = gateway.get.call_args.args[0]
    assert path == "/supplies/purchase-order-otd/panel"
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == "01"
    assert "branch" in params and params["branch"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_negative_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.manage"})
    client = create_app().test_client()
    response = client.get(
        "/deliveries/late?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_unauthenticated(mock_resolve, mock_validate):
    client = create_app().test_client()
    response = client.get("/deliveries/late?branch=01")
    assert response.status_code == 401
    mock_validate.assert_not_called()
    mock_resolve.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_core_unavailable_fail_closed(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core down")
    client = create_app().test_client()
    response = client.get(
        "/deliveries/late?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 503


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_invalid_branch_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    response = client.get(
        "/deliveries/late?branch=99",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 422
    assert response.get_json()["code"] == "unprocessable"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_invalid_status_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    response = client.get(
        "/deliveries/late?branch=01&status=pending",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 422


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_upstream_5xx_maps_502(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error",
        status_code=503,
    )
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/deliveries/late?branch=01&start_date=2026-09-01&end_date=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_consolidated_one_leg_failure_502(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()

    def _side_effect(path, **kwargs):
        branch = kwargs["params"]["branch"]
        if branch == "02":
            raise DelpiApiGatewayError("api-delpi server error", status_code=503)
        return _panel_payload(branch=branch, items=[], total=0)

    gateway.get.side_effect = _side_effect
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/deliveries/late?branch=01&branch=02&start_date=2026-09-01&end_date=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_consolidated_never_omits_branch(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.side_effect = lambda path, **kwargs: _panel_payload(
        branch=kwargs["params"]["branch"],
        items=[],
        total=0,
    )
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/deliveries/late?start_date=2026-09-01&end_date=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert gateway.get.call_count == 2
    for call in gateway.get.call_args_list:
        assert call.kwargs["params"]["branch"] in {"01", "02"}
        assert call.kwargs["params"]["branch"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_empty_is_200(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.return_value = _panel_payload(branch="01", items=[], total=0)
    with patch(
        "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway",
        return_value=gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/deliveries/late?branch=01&start_date=2026-09-01&end_date=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["items"] == []
    assert body["total"] == 0
