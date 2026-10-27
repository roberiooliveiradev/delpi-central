"""HTTP BFF — configurable Comex analysis routes (PROC-0076.COMEX.S2/S3).

Product catalog proxy, NCM governance lifecycle and personal saved
views. AuthZ stays fail-closed on ``supplies.access``; homologation
decisions additionally require ``supplies.manage`` inside the service.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser

_AUTH_MIDDLEWARE = (
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
_JWT = "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate"
_SERVICE = (
    "app.interfaces.http.routes.market_intelligence_routes.ComexAnalysisService"
)

BUYER_ID = "22222222-2222-2222-2222-222222222222"


def _user(*, manage=False) -> EffectiveUser:
    permissions = {"supplies.access"}
    if manage:
        permissions.add("supplies.manage")
    return EffectiveUser(
        id=BUYER_ID,
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


def _auth(mock_resolve, mock_validate, *, manage=False):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(manage=manage)


def _client():
    return create_app().test_client()


# --- product catalog proxy ----------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_product_search_proxies_allowlisted_params(mock_resolve, mock_validate):
    _auth(mock_resolve, mock_validate)
    service = MagicMock()
    service.search_products.return_value = {
        "items": [
            {
                "code": "FIO-CU-001",
                "type": "MP",
                "ncm_code": "74081190",
                "ncm_status": "present",
            }
        ],
        "total": 1,
    }
    client = _client()
    with patch(_SERVICE, return_value=service):
        response = client.get(
            "/market-intelligence/comex/products/search"
            "?product_type=MP&description=cobre&page=1&evil_param=x",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["items"][0]["ncm_status"] == "present"
    args = service.search_products.call_args.kwargs["args"]
    assert args["product_type"] == "MP"
    assert args["description"] == "cobre"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_product_search_forbidden_without_access(mock_resolve, mock_validate):
    _auth(mock_resolve, mock_validate)
    mock_resolve.return_value = _user()
    mock_resolve.return_value.permissions = set()
    client = _client()
    response = client.get(
        "/market-intelligence/comex/products/search",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


def test_product_search_unauthenticated():
    client = _client()
    response = client.get("/market-intelligence/comex/products/search")
    assert response.status_code == 401


# --- governance ----------------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_governance_create_returns_201(mock_resolve, mock_validate):
    _auth(mock_resolve, mock_validate)
    service = MagicMock()
    service.request_ncm.return_value = {
        "governance_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "ncm_code": "74081190",
        "status": "pending_fiscal_review",
        "revision": 1,
    }
    client = _client()
    with patch(_SERVICE, return_value=service):
        response = client.post(
            "/market-intelligence/comex/ncm-governance",
            json={
                "ncm_code": "74081190",
                "description": "Fios de cobre",
                "ncm_version": "NCM 2022",
                "product_codes": ["FIO-CU-001"],
            },
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 201
    assert response.get_json()["status"] == "pending_fiscal_review"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_governance_transition_maps_service_errors(mock_resolve, mock_validate):
    from app.application.services.comex_analysis_service import (
        ComexForbiddenError,
        ComexValidationError,
    )

    _auth(mock_resolve, mock_validate)
    service = MagicMock()
    service.transition.side_effect = ComexForbiddenError("requires manage")
    client = _client()
    with patch(_SERVICE, return_value=service):
        response = client.post(
            "/market-intelligence/comex/ncm-governance/"
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/transition",
            json={"to_status": "approved"},
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403

    service.transition.side_effect = ComexValidationError(
        "bad", code="invalid_status"
    )
    with patch(_SERVICE, return_value=service):
        response = client.post(
            "/market-intelligence/comex/ncm-governance/"
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/transition",
            json={"to_status": "nope"},
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


# --- saved views ----------------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_view_crud_routes(mock_resolve, mock_validate):
    _auth(mock_resolve, mock_validate)
    service = MagicMock()
    view = {
        "view_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "owner_user_id": BUYER_ID,
        "name": "Cobre importado",
        "view_mode": "chart",
    }
    service.create_view.return_value = view
    service.get_view.return_value = view
    service.list_views.return_value = [view]
    client = _client()
    headers = {"Authorization": "Bearer tok"}
    with patch(_SERVICE, return_value=service):
        created = client.post(
            "/market-intelligence/comex/views",
            json={"name": "Cobre importado"},
            headers=headers,
        )
        listed = client.get("/market-intelligence/comex/views", headers=headers)
        deleted = client.delete(
            "/market-intelligence/comex/views/"
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            headers=headers,
        )
    assert created.status_code == 201
    assert listed.get_json()["items"][0]["name"] == "Cobre importado"
    assert deleted.status_code == 204


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_view_not_found_maps_404(mock_resolve, mock_validate):
    from app.application.services.comex_analysis_service import (
        ComexNotFoundError,
    )

    _auth(mock_resolve, mock_validate)
    service = MagicMock()
    service.get_view.side_effect = ComexNotFoundError("saved view not found")
    client = _client()
    with patch(_SERVICE, return_value=service):
        response = client.get(
            "/market-intelligence/comex/views/"
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
