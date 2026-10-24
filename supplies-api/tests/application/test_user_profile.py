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
                "supplies.access",
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
            _user(permissions={"supplies.access", "supplies.unit.filial-01"}),
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
                "supplies.access",
                "supplies.manage",
            }
        ),
        OTHER_ID,
    )
    assert result["isSelf"] is False
    assert result["name"] == "Ana Admin"
    assert result["email"] == "ana@delpi.com.br"
    # Core-authorized flag reveals the real professional address (never masked).
    core.lookup_directory_users.assert_called_once_with(
        access_token="token", user_ids=[OTHER_ID], reveal_email=True
    )
    assert result["capabilities"] is None
    assert result["allowedUnits"] == []


def test_patch_self_rejects_branch_outside_units():
    repo = MagicMock()
    repo.get.return_value = None
    service = UserProfileService(preferences=PreferencesService(repository=repo))
    with pytest.raises(AuthorizationError):
        service.patch(
            _user(permissions={"supplies.access", "supplies.unit.filial-01"}),
            SELF_ID,
            {"preferences": {"defaultBranch": "99"}},
        )


def test_patch_other_forbidden():
    service = UserProfileService()
    with pytest.raises(AuthorizationError):
        service.patch(
            _user(
                permissions={
                    "supplies.access",
                    "supplies.manage",
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
        permissions={"supplies.access", "supplies.unit.filial-01"}
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
    mock_resolve.return_value = _user(permissions={"supplies.access"})
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


# --- related purchase requests (USERS.PROFILE.S1) ------------------------------


def _mapped(pid: str, uid: str = OTHER_ID) -> dict:
    return {
        "protheus_user_id": pid,
        "user_id": uid,
        "mapping_status": "mapped",
    }


def test_related_self_positive_resolves_bond_and_forwards():
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": _mapped("000007", SELF_ID),
    }
    pr = MagicMock()
    pr.list_purchase_requests.return_value = {
        "items": [{"request_number": "178764", "branch": "01"}],
        "total": 1,
        "page": 1,
        "page_size": 5,
    }
    identity = MagicMock()
    identity.enrich_payload.side_effect = lambda data, **_: data
    service = UserProfileService(
        core_gateway=core,
        purchase_requests_gateway=pr,
        requester_identity=identity,
    )
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access", "supplies.unit.filial-01"}),
        SELF_ID,
        branches=["01"],
        page=1,
        page_size=5,
    )
    assert result["total"] == 1
    assert result["protheus_user_ids"] == ["000007"]
    params = dict(pr.list_purchase_requests.call_args.kwargs["params"])
    assert params["requester_user_id"] == "000007"
    assert params["branch"] == "01"
    assert params["sort_by"] == "issue_date"
    # Explicit history floor — never the producer's implicit lookback.
    assert params["date_from"] == "2000-01-01"
    # Target resolution — never the actor as substitute.
    core.lookup_protheus_identities.assert_called_once_with(user_ids=[SELF_ID])


def test_related_client_sort_passthrough():
    """Profile reuses the real PR table: server-side sort is client-driven."""
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": _mapped("000007", SELF_ID),
    }
    pr = MagicMock()
    pr.list_purchase_requests.return_value = {"items": [], "total": 0}
    service = UserProfileService(
        core_gateway=core,
        purchase_requests_gateway=pr,
        requester_identity=MagicMock(
            enrich_payload=MagicMock(side_effect=lambda data, **_: data)
        ),
    )
    service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
        sort_by="request_number",
        sort_dir="asc",
    )
    params = dict(pr.list_purchase_requests.call_args.kwargs["params"])
    assert params["sort_by"] == "request_number"
    assert params["sort_dir"] == "asc"


def test_related_no_filter_expands_actor_authorized_units():
    """Producer requires ≥1 branch: empty filter = actor's own units."""
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": _mapped("000007", SELF_ID),
    }
    pr = MagicMock()
    pr.list_purchase_requests.return_value = {"items": [], "total": 0}
    service = UserProfileService(
        core_gateway=core,
        purchase_requests_gateway=pr,
        requester_identity=MagicMock(
            enrich_payload=MagicMock(side_effect=lambda data, **_: data)
        ),
    )
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
    )
    params = pr.list_purchase_requests.call_args.kwargs["params"]
    assert sorted(v for k, v in params if k == "branch") == ["01", "02"]
    assert dict(params)["date_from"] == "2000-01-01"
    assert result["total"] == 0


def test_related_lookup_failure_is_unavailable_not_unmapped():
    """Core lookup outage is degradation — never requester_unmapped."""
    core = MagicMock()
    core.lookup_protheus_identities.return_value = None
    pr = MagicMock()
    service = UserProfileService(core_gateway=core, purchase_requests_gateway=pr)
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
    )
    assert result["error"] == "identity_lookup_unavailable"
    assert result["requester_unmapped"] is False
    pr.list_purchase_requests.assert_not_called()


def test_related_unauthorized_branch_negative():
    core = MagicMock()
    service = UserProfileService(core_gateway=core)
    with pytest.raises(AuthorizationError):
        service.related_purchase_requests(
            _user(permissions={"supplies.access"}),
            SELF_ID,
            branches=["99"],
        )


def test_related_other_negative_without_admin():
    service = UserProfileService()
    with pytest.raises(AuthorizationError):
        service.related_purchase_requests(
            _user(permissions={"supplies.access", "supplies.unit.filial-01"}),
            OTHER_ID,
        )


def test_related_other_sibling_admin_ok():
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {}
    service = UserProfileService(core_gateway=core)
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access", "supplies.manage"}),
        OTHER_ID,
    )
    assert result["items"] == []
    assert result["requester_unmapped"] is True


def test_related_unmapped_no_gateway_call():
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": {**_mapped("000007", SELF_ID), "mapping_status": "revoked"},
    }
    pr = MagicMock()
    service = UserProfileService(core_gateway=core, purchase_requests_gateway=pr)
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
    )
    assert result["items"] == []
    assert result["requester_unmapped"] is True
    pr.list_purchase_requests.assert_not_called()


def test_related_multiple_bonds_forward_all_ids():
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": _mapped("000007", SELF_ID),
        "000042": _mapped("000042", SELF_ID),
    }
    pr = MagicMock()
    pr.list_purchase_requests.return_value = {"items": [], "total": 0}
    identity = MagicMock()
    identity.enrich_payload.side_effect = lambda data, **_: data
    service = UserProfileService(
        core_gateway=core,
        purchase_requests_gateway=pr,
        requester_identity=identity,
    )
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
    )
    params = pr.list_purchase_requests.call_args.kwargs["params"]
    pids = [value for key, value in params if key == "requester_user_id"]
    assert sorted(pids) == ["000007", "000042"]
    assert result["protheus_user_ids"] == ["000007", "000042"]


def test_related_gateway_failure_degrades_partial():
    core = MagicMock()
    core.lookup_protheus_identities.return_value = {
        "000007": _mapped("000007", SELF_ID),
    }
    pr = MagicMock()
    pr.list_purchase_requests.side_effect = RuntimeError("upstream down")
    service = UserProfileService(core_gateway=core, purchase_requests_gateway=pr)
    result = service.related_purchase_requests(
        _user(permissions={"supplies.access"}),
        SELF_ID,
    )
    assert result["error"] == "related_requests_unavailable"
    assert result["items"] == []


def test_photo_self_positive():
    core = MagicMock()
    core.get_person_profile_photo.return_value = (b"img", "image/jpeg", "a.jpg")
    service = UserProfileService(core_gateway=core)
    photo = service.photo(_user(permissions={"supplies.access"}), SELF_ID)
    assert photo == (b"img", "image/jpeg", "a.jpg")


def test_photo_other_negative_without_admin():
    service = UserProfileService()
    with pytest.raises(AuthorizationError):
        service.photo(
            _user(permissions={"supplies.access"}),
            OTHER_ID,
        )


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_related_self_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.access", "supplies.unit.filial-01"}
    )
    with patch(
        "app.interfaces.http.routes.users_routes.UserProfileService"
    ) as service_cls:
        instance = service_cls.return_value
        instance.related_purchase_requests.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 5,
            "protheus_user_ids": ["000007"],
        }
        client = create_app().test_client()
        response = client.get(
            f"/users/{SELF_ID}/related-requests",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    assert response.get_json()["protheus_user_ids"] == ["000007"]


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_photo_missing_is_404(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    with patch(
        "app.interfaces.http.routes.users_routes.UserProfileService"
    ) as service_cls:
        instance = service_cls.return_value
        instance.photo.return_value = None
        client = create_app().test_client()
        response = client.get(
            f"/users/{SELF_ID}/photo",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
