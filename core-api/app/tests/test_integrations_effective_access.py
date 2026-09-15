"""TV-GPI-004B4 — Core S2S effective-access-by-subject contract tests."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.get_effective_access_by_subject_use_case import (
    EffectiveAccessIdentityNotFoundError,
    EffectiveAccessUnavailableError,
    GetEffectiveAccessBySubjectUseCase,
)
from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


EFFECTIVE_TOKEN = "effective-access-secret"
INTEGRATIONS_TOKEN = "integrations-shared-secret"


def _headers(token: str | None = EFFECTIVE_TOKEN) -> dict[str, str]:
    if token is None:
        return {}
    return {"X-Delpi-Service-Token": token}


def test_controller_registered_in_create_app():
    from pathlib import Path

    create_app_src = (
        Path(__file__).resolve().parents[1] / "create_app.py"
    ).read_text(encoding="utf-8")
    assert "integrations_effective_access_bp" in create_app_src
    assert "register_blueprint(integrations_effective_access_bp)" in create_app_src


def test_missing_service_auth_rejected(client):
    with patch.dict(
        os.environ,
        { "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN },
        clear=False,
    ):
        response = client.get(f"/integrations/effective-access/subjects/{uuid4()}")
    assert response.status_code == 401


def test_invalid_service_auth_rejected(client):
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        response = client.get(
            f"/integrations/effective-access/subjects/{uuid4()}",
            headers=_headers("wrong"),
        )
    assert response.status_code == 403


def test_integrations_token_alone_does_not_authorize(client):
    """CALLER_BINDING: shared integrations secret must not unlock this capability."""
    with patch.dict(
        os.environ,
        {
            "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN,
            "CORE_API_INTEGRATIONS_SERVICE_TOKEN": INTEGRATIONS_TOKEN,
        },
        clear=False,
    ):
        response = client.get(
            f"/integrations/effective-access/subjects/{uuid4()}",
            headers=_headers(INTEGRATIONS_TOKEN),
        )
    assert response.status_code == 403


def test_user_bearer_alone_does_not_become_s2s_auth(client):
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        response = client.get(
            f"/integrations/effective-access/subjects/{uuid4()}",
            headers={"Authorization": "Bearer user-jwt-not-a-service-token"},
        )
    assert response.status_code == 403


def test_malformed_sub_rejected(client):
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        response = client.get(
            "/integrations/effective-access/subjects/not-a-uuid",
            headers=_headers(),
        )
    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "validation_error"


def test_unknown_subject_not_found_no_email_fallback(client):
    subject = uuid4()
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = None
            uow_cls.return_value = uow

            response = client.get(
                f"/integrations/effective-access/subjects/{subject}",
                headers=_headers(),
            )

    assert response.status_code == 404
    assert response.get_json()["errors"][0]["code"] == "identity_not_found"
    uow.users.get_by_id.assert_called_once_with(subject)
    assert not hasattr(uow.users, "get_by_email") or not uow.users.get_by_email.called


def test_valid_trusted_service_returns_authoritative_permissions(client):
    subject = uuid4()
    user = SimpleNamespace(id=subject, is_superadmin=False)
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = user
            uow_cls.return_value = uow

            with patch(
                "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
            ) as resolver_cls:
                resolver_cls.return_value.resolve.return_value = [
                    "tv-dashboard.read",
                    "tv-dashboard.write",
                ]
                response = client.get(
                    f"/integrations/effective-access/subjects/{subject}",
                    headers=_headers(),
                )

    assert response.status_code == 200
    data = response.get_json()
    assert data["userId"] == str(subject)
    assert data["keycloakSubject"] == str(subject)
    assert data["isSuperadmin"] is False
    assert data["permissions"] == ["tv-dashboard.read", "tv-dashboard.write"]
    # Caller cannot supply permissions — only resolver output is returned.
    assert "roles" not in data


def test_subject_with_no_permissions_is_valid_negative(client):
    subject = uuid4()
    user = SimpleNamespace(id=subject, is_superadmin=False)
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = user
            uow_cls.return_value = uow
            with patch(
                "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
            ) as resolver_cls:
                resolver_cls.return_value.resolve.return_value = []
                response = client.get(
                    f"/integrations/effective-access/subjects/{subject}",
                    headers=_headers(),
                )

    assert response.status_code == 200
    assert response.get_json()["permissions"] == []
    assert response.get_json()["isSuperadmin"] is False


def test_superadmin_semantics_match_resolver(client):
    subject = uuid4()
    user = SimpleNamespace(id=subject, is_superadmin=True)
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = user
            uow_cls.return_value = uow
            with patch(
                "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
            ) as resolver_cls:
                resolver_cls.return_value.resolve.return_value = ["a", "b", "c"]
                response = client.get(
                    f"/integrations/effective-access/subjects/{subject}",
                    headers={"Authorization": f"Bearer {EFFECTIVE_TOKEN}"},
                )
                resolver_cls.return_value.resolve.assert_called_once_with(
                    subject, True
                )

    assert response.status_code == 200
    assert response.get_json()["isSuperadmin"] is True
    assert response.get_json()["permissions"] == ["a", "b", "c"]


def test_permission_backend_unavailable_returns_503(client):
    subject = uuid4()
    user = SimpleNamespace(id=subject, is_superadmin=False)
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = user
            uow_cls.return_value = uow
            with patch(
                "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
            ) as resolver_cls:
                resolver_cls.return_value.resolve.side_effect = RuntimeError("db down")
                response = client.get(
                    f"/integrations/effective-access/subjects/{subject}",
                    headers=_headers(),
                )

    assert response.status_code == 503
    assert response.get_json()["errors"][0]["code"] == "authorization_unavailable"


def test_use_case_rejects_unknown_subject_without_email():
    uow = MagicMock()
    uow.users.get_by_id.return_value = None
    subject = uuid4()
    with pytest.raises(EffectiveAccessIdentityNotFoundError):
        GetEffectiveAccessBySubjectUseCase(uow).execute(keycloak_subject=subject)
    uow.users.get_by_email.assert_not_called()


def test_use_case_maps_resolver_failure_to_unavailable():
    subject = uuid4()
    uow = MagicMock()
    uow.users.get_by_id.return_value = SimpleNamespace(id=subject, is_superadmin=False)
    with patch(
        "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
    ) as resolver_cls:
        resolver_cls.return_value.resolve.side_effect = RuntimeError("boom")
        with pytest.raises(EffectiveAccessUnavailableError):
            GetEffectiveAccessBySubjectUseCase(uow).execute(keycloak_subject=subject)


def test_bearer_effective_access_reaches_use_case_on_owned_path(client):
    subject = uuid4()
    user = SimpleNamespace(id=subject, is_superadmin=False)
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_effective_access_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = MagicMock()
            uow.__enter__.return_value = uow
            uow.__exit__.return_value = False
            uow.users.get_by_id.return_value = user
            uow_cls.return_value = uow
            with patch(
                "app.application.use_cases.get_effective_access_by_subject_use_case.PermissionResolver"
            ) as resolver_cls:
                resolver_cls.return_value.resolve.return_value = ["tv-dashboard.read"]
                response = client.get(
                    f"/integrations/effective-access/subjects/{subject}",
                    headers={"Authorization": f"Bearer {EFFECTIVE_TOKEN}"},
                )

    assert response.status_code == 200
    assert response.get_json()["permissions"] == ["tv-dashboard.read"]


def test_effective_access_bearer_cannot_bypass_jwt_on_me(client, app):
    """Path-scope: same secret must not short-circuit JWT on /me."""
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        # create_app("testing") skips authenticate; enable middleware for this proof.
        app.config["TESTING"] = False
        try:
            response = client.get(
                "/me",
                headers={"Authorization": f"Bearer {EFFECTIVE_TOKEN}"},
            )
        finally:
            app.config["TESTING"] = True

    assert response.status_code == 401
    assert response.get_json()["errors"][0]["code"] == "invalid_token"


def test_effective_access_bearer_cannot_authorize_admin_route(client, app):
    with patch.dict(
        os.environ,
        {"CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN},
        clear=False,
    ):
        app.config["TESTING"] = False
        try:
            response = client.get(
                "/admin/statistics",
                headers={"Authorization": f"Bearer {EFFECTIVE_TOKEN}"},
            )
        finally:
            app.config["TESTING"] = True

    assert response.status_code == 401
    assert response.get_json()["errors"][0]["code"] == "invalid_token"


def test_effective_access_bearer_not_authorized_as_unrelated_integration(client, app):
    with patch.dict(
        os.environ,
        {
            "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN": EFFECTIVE_TOKEN,
            "CORE_API_INTEGRATIONS_SERVICE_TOKEN": INTEGRATIONS_TOKEN,
        },
        clear=False,
    ):
        app.config["TESTING"] = False
        try:
            response = client.get(
                "/integrations/notifications",
                headers={"Authorization": f"Bearer {EFFECTIVE_TOKEN}"},
            )
        finally:
            app.config["TESTING"] = True

    assert response.status_code != 200
    assert response.status_code >= 400
