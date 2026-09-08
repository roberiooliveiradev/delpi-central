from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import jsonify

from app.application.services.authorization_service import AuthorizationService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.exceptions import CoreApiUnavailableError
from app.interfaces.http.auth_decorators import require_permission, require_unit


@pytest.fixture()
def app():
    application = create_app()
    application.config["TESTING"] = True

    @application.get("/_test/secure")
    @require_permission("supplies.portal.access")
    def secure():
        return jsonify({"ok": True}), 200

    @application.get("/_test/unit")
    @require_permission("supplies.operations.access")
    @require_unit("branch")
    def unit_secure():
        return jsonify({"ok": True}), 200

    return application


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def _identity():
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
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


def test_public_health_skips_auth(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_missing_bearer_returns_401(client):
    response = client.get("/_test/secure")
    assert response.status_code == 401


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_permission_granted(mock_resolve, mock_validate, client):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})

    response = client.get(
        "/_test/secure",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_permission_denied(mock_resolve, mock_validate, client):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.analytics.access"})

    response = client.get(
        "/_test/secure",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_core_unavailable_returns_503(mock_resolve, mock_validate, client):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core API request failed")

    response = client.get(
        "/_test/secure",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 503
    assert response.get_json()["detail"] == "Core API request failed"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_jwt_claims_permissions_are_ignored(mock_resolve, mock_validate, client):
    """Even if JWT carried permissions, AuthZ uses only Core /me payload."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=set())

    response = client.get(
        "/_test/secure",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403
    mock_resolve.assert_called_once()


def test_unit_authorization_positive_and_negative():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )
    service.require_unit(user, "01")
    with pytest.raises(Exception):
        service.require_unit(user, "02")


def test_legacy_unit_aliases():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user(permissions={"estoque-seguranca.view.filial-es"})
    assert service.allowed_units(user) == ["02"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_unit_route_filial_cruzada(mock_resolve, mock_validate, client):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.operations.access",
            "supplies.unit.filial-01",
        }
    )

    denied = client.get(
        "/_test/unit?branch=02",
        headers={"Authorization": "Bearer good-token"},
    )
    assert denied.status_code == 403

    allowed = client.get(
        "/_test/unit?branch=01",
        headers={"Authorization": "Bearer good-token"},
    )
    assert allowed.status_code == 200


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_superadmin_from_core_only(mock_resolve, mock_validate, client):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions=set(), is_superadmin=True)

    response = client.get(
        "/_test/secure",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 200
