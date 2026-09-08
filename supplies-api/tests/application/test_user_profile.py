from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.application.services.preferences_service import PreferencesService
from app.application.services.user_profile_service import UserProfileService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.exceptions import AuthorizationError


SELF_ID = "22222222-2222-2222-2222-222222222222"
OTHER_ID = "33333333-3333-3333-3333-333333333333"


def _user(*, permissions: set[str], user_id: str = SELF_ID) -> EffectiveUser:
    return EffectiveUser(
        id=user_id,
        email="buyer@delpi.com.br",
        name="Buyer Silva",
        permissions=permissions,
        is_superadmin=False,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer Silva",
    )


def test_get_self_positive():
    prefs = MagicMock()
    prefs.get.return_value = {
        "userId": SELF_ID,
        "defaultBranch": "01",
        "tableDensity": "compact",
    }
    caps = MagicMock()
    caps.resolve.return_value = {
        "userId": SELF_ID,
        "capabilities": {"portal": True, "analytics": False},
        "allowedUnits": ["01"],
        "aliasesDoNotGrantAppAccess": True,
    }
    service = UserProfileService(preferences=prefs, capabilities=caps)
    result = service.get(
        _user(
            permissions={
                "supplies.portal.access",
                "supplies.unit.filial-01",
            }
        ),
        SELF_ID,
    )
    assert result["isSelf"] is True
    assert result["name"] == "Buyer Silva"
    assert result["preferences"]["defaultBranch"] == "01"
    assert result["allowedUnits"] == ["01"]
    assert result["capabilities"]["portal"] is True


def test_get_other_negative_without_admin():
    service = UserProfileService()
    with pytest.raises(AuthorizationError):
        service.get(
            _user(permissions={"supplies.portal.access", "supplies.unit.filial-01"}),
            OTHER_ID,
        )


def test_get_other_sibling_admin_ok():
    repo = MagicMock()
    repo.get.return_value = None
    core = MagicMock()
    core.lookup_directory_users.return_value = {
        OTHER_ID: {"id": OTHER_ID, "name": "Ana Admin", "email": "ana@delpi.com.br"},
    }
    service = UserProfileService(preferences_repository=repo, core_gateway=core)
    result = service.get(
        _user(
            permissions={
                "supplies.portal.access",
                "supplies.administration.manage",
            }
        ),
        OTHER_ID,
    )
    assert result["isSelf"] is False
    assert result["name"] == "Ana Admin"
    assert result["email"] == "ana@delpi.com.br"
    assert result["capabilities"] is None
    assert result["allowedUnits"] == []


def test_patch_self_rejects_branch_outside_units():
    repo = MagicMock()
    repo.get.return_value = None
    service = UserProfileService(preferences=PreferencesService(repository=repo))
    with pytest.raises(AuthorizationError):
        service.patch(
            _user(permissions={"supplies.portal.access", "supplies.unit.filial-01"}),
            SELF_ID,
            {"preferences": {"defaultBranch": "02"}},
        )


def test_patch_other_forbidden():
    service = UserProfileService()
    with pytest.raises(AuthorizationError):
        service.patch(
            _user(
                permissions={
                    "supplies.portal.access",
                    "supplies.administration.manage",
                }
            ),
            OTHER_ID,
            {"preferences": {"tableDensity": "compact"}},
        )


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_get_self(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.portal.access", "supplies.unit.filial-01"}
    )
    with patch(
        "app.interfaces.http.routes.users_routes.UserProfileService"
    ) as service_cls:
        instance = service_cls.return_value
        instance.get.return_value = {
            "userId": SELF_ID,
            "name": "Buyer Silva",
            "email": "buyer@delpi.com.br",
            "isSelf": True,
            "preferences": {"defaultBranch": "01", "tableDensity": "comfortable"},
            "capabilities": {"portal": True},
            "allowedUnits": ["01"],
        }
        client = create_app().test_client()
        response = client.get(
            f"/users/{SELF_ID}/profile",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["isSelf"] is True


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_get_other_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    with patch(
        "app.interfaces.http.routes.users_routes.UserProfileService"
    ) as service_cls:
        instance = service_cls.return_value
        instance.get.side_effect = AuthorizationError("Forbidden")
        client = create_app().test_client()
        response = client.get(
            f"/users/{OTHER_ID}/profile",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 403
