from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGatewayError,
)


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
            "supplies.access",
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
def test_list_negative_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.unit.filial-01"})
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
        permissions={"supplies.unit.filial-01", "supplies.manage"}
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
            "supplies.access",
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


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_multi_unit_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.access",
            "supplies.unit.filial-01",
            "supplies.unit.filial-02",
        }
    )
    gateway = MagicMock()
    gateway.list_purchase_requests.return_value = {
        "success": True,
        "data": {"items": [], "total": 0},
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests?branch=01&branch=02",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_multi_unit_sibling_mixed_scope_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.unit.filial-01"})
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests?branch=01&branch=02",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_empty_unit_selection_fail_closed(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.access",
            "supplies.unit.filial-01",
        }
    )
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_positive_requires_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get_summary.return_value = {
        "success": True,
        "data": {"total_requests": 3, "buckets": {"ordering": 1}},
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/summary?branch=01&overall_stage=completed",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["total_requests"] == 3
    gateway.get_summary.assert_called_once()
    forwarded = gateway.get_summary.call_args.kwargs["query_string"]
    assert "branch=01" in forwarded
    assert "overall_stage=completed" in forwarded


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_negative_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=set())
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests/summary?branch=01",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_summary_upstream_unavailable(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get_summary.side_effect = PurchaseRequestsGatewayError(
        "purchase-requests-api timeout"
    )
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/summary?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_list_enriches_requester_via_identity_service(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    gateway = MagicMock()
    gateway.list_purchase_requests.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "request_number": "100",
                    "requester": {"protheus_user_id": "000123", "name": "ELAINE"},
                }
            ],
            "total": 1,
        },
    }
    identity = MagicMock()
    identity.enrich_payload.side_effect = lambda payload, *, access_token: {
        **payload,
        "items": [
            {
                **item,
                "requester": {**item["requester"], "display_name": "Elaine Souza"},
            }
            for item in payload.get("items", [])
        ],
    }
    with (
        patch(
            "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
            gateway,
        ),
        patch(
            "app.interfaces.http.routes.purchase_requests_routes._REQUESTER_IDENTITY",
            identity,
        ),
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["requester"]["display_name"] == "Elaine Souza"
    assert item["requester"]["name"] == "ELAINE"
    identity.enrich_payload.assert_called_once()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requester_photo_streams_mapped_user_photo(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    identity = MagicMock()
    identity.get_requester_photo.return_value = (b"\x89PNG", "image/png", "e.png")
    scope = MagicMock()
    scope.is_allowed.return_value = True
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._REQUESTER_IDENTITY",
        identity,
    ), patch(
        "app.interfaces.http.routes.purchase_requests_routes._PHOTO_SCOPE",
        scope,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/requesters/000123/photo?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.data == b"\x89PNG"
    assert response.mimetype == "image/png"
    identity.get_requester_photo.assert_called_once_with("000123")
    scope.is_allowed.assert_called_once()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requester_photo_404_when_unmapped_or_absent(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    identity = MagicMock()
    identity.get_requester_photo.return_value = None
    scope = MagicMock()
    scope.is_allowed.return_value = True
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._REQUESTER_IDENTITY",
        identity,
    ), patch(
        "app.interfaces.http.routes.purchase_requests_routes._PHOTO_SCOPE",
        scope,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/requesters/999/photo?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404


def test_requester_photo_requires_auth():
    client = create_app().test_client()
    response = client.get("/purchase-requests/requesters/000123/photo?branch=01")
    assert response.status_code == 401


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requester_photo_404_outside_authorized_universe(
    mock_resolve, mock_validate
):
    """Mapped but outside the caller's requester facet -> 404; Core untouched."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    identity = MagicMock()
    scope = MagicMock()
    scope.is_allowed.return_value = False
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._REQUESTER_IDENTITY",
        identity,
    ), patch(
        "app.interfaces.http.routes.purchase_requests_routes._PHOTO_SCOPE",
        scope,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/requesters/000999/photo?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    identity.get_requester_photo.assert_not_called()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requester_photo_403_without_branch(mock_resolve, mock_validate):
    """Unit scope is mandatory — photo cannot be fetched outside unit context."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests/requesters/000123/photo",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requester_photo_403_unknown_branch(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    response = client.get(
        "/purchase-requests/requesters/000123/photo?branch=99",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_requesters_facet_enriched_with_display_name(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    gateway = MagicMock()
    gateway.list_requesters.return_value = {
        "success": True,
        "data": {
            "items": [{"protheus_user_id": "000123", "name": "ELAINE"}]
        },
    }
    identity = MagicMock()
    identity.enrich_payload.side_effect = lambda payload, *, access_token: {
        **payload,
        "items": [
            {**item, "display_name": "Elaine Souza"}
            for item in payload.get("items", [])
        ],
    }
    with (
        patch(
            "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
            gateway,
        ),
        patch(
            "app.interfaces.http.routes.purchase_requests_routes._REQUESTER_IDENTITY",
            identity,
        ),
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/requesters?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["items"][0]["display_name"] == "Elaine Souza"
    identity.enrich_payload.assert_called_once()


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_cost_centers_facet_passes_through(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    gateway = MagicMock()
    gateway.list_cost_centers.return_value = {
        "success": True,
        "data": {
            "items": [{"branch": "01", "code": "0413", "description": "Produção"}]
        },
    }
    with patch(
        "app.interfaces.http.routes.purchase_requests_routes._GATEWAY",
        gateway,
    ):
        client = create_app().test_client()
        response = client.get(
            "/purchase-requests/cost-centers?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["items"][0]["code"] == "0413"
