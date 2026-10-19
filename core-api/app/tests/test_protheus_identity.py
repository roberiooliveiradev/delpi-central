from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from flask import g

from app.create_app import create_app
from app.domain.entities.user_protheus_identity import UserProtheusIdentity
from app.domain.services.protheus_user_candidate_resolver import (
    pick_protheus_user_candidate,
)
from app.infrastructure.gateways.delpi_protheus_users_gateway import (
    TotvsLookupUnavailableError,
)


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _identity(user_id, *, protheus_user_id="000234"):
    now = datetime.now(timezone.utc)
    return UserProtheusIdentity(
        user_id=user_id,
        protheus_user_id=protheus_user_id,
        protheus_user_code="YAGO.ROCHA",
        mapping_status="mapped",
        mapping_source="email_match",
        verified=True,
        updated_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def test_pick_candidate_preserves_single_match():
    candidate = {"protheus_user_id": "000001", "name": "A", "code": "A"}
    assert pick_protheus_user_candidate([candidate]) is candidate


def test_pick_candidate_does_not_silent_pick_ambiguous_without_name():
    candidates = [
        {"protheus_user_id": "1", "name": "A", "code": "A"},
        {"protheus_user_id": "2", "name": "B", "code": "B"},
    ]
    assert pick_protheus_user_candidate(candidates) is None


def test_admin_get_protheus_identity_requires_auth(client):
    user_id = uuid4()
    response = client.get(
        f"/admin/rbac/users/{user_id}/external-identities/protheus"
    )
    assert response.status_code == 401


@patch("app.interfaces.http.rbac_controller.GetUserProtheusIdentityUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_admin_get_protheus_identity_forbidden(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=False, permissions=[])
            response = client.get(
                f"/admin/rbac/users/{user_id}/external-identities/protheus"
            )
    assert response.status_code == 403
    mock_uc.return_value.execute.assert_not_called()


@patch("app.interfaces.http.rbac_controller.GetUserProtheusIdentityUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_admin_get_protheus_identity_success(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uow.return_value.__enter__.return_value.users.get_by_id.return_value = (
        SimpleNamespace(id=user_id, active=True)
    )
    mock_uc.return_value.execute.return_value = _identity(user_id).to_dict()

    with app.app_context():
        with client:
            g.current_user = MagicMock(
                is_superadmin=False,
                permissions=["rbac.manage", "users.manage"],
            )
            response = client.get(
                f"/admin/rbac/users/{user_id}/external-identities/protheus"
            )

    assert response.status_code == 200
    body = response.get_json()
    assert body["mapping"]["protheus_user_id"] == "000234"


@patch(
    "app.interfaces.http.rbac_controller.SyncUserProtheusIdentityByEmailUseCase"
)
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_admin_sync_uses_core_email_not_body(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uc.return_value.execute.return_value = {
        "mapping": _identity(user_id).to_dict(),
        "protheus_user": {
            "protheus_user_id": "000234",
            "code": "YAGO.ROCHA",
            "name": "Yago",
            "email": "yago@delpi.com.br",
        },
        "synced_by_email": "yago@delpi.com.br",
    }

    with app.app_context():
        with client:
            g.current_user = MagicMock(
                id=uuid4(),
                is_superadmin=True,
                permissions=["rbac.manage", "users.manage"],
            )
            response = client.post(
                f"/admin/rbac/users/{user_id}/external-identities/protheus/sync",
                json={"email": "attacker@evil.com"},
            )

    assert response.status_code == 200
    mock_uc.return_value.execute.assert_called_once()
    kwargs = mock_uc.return_value.execute.call_args.kwargs
    assert "email" not in kwargs
    assert kwargs["user_id"] == user_id


@patch(
    "app.interfaces.http.rbac_controller.SyncUserProtheusIdentityByEmailUseCase"
)
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_admin_sync_totvs_unavailable(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uc.return_value.execute.side_effect = TotvsLookupUnavailableError(
        "TOTVS down"
    )

    with app.app_context():
        with client:
            g.current_user = MagicMock(
                id=uuid4(),
                is_superadmin=True,
                permissions=[],
            )
            response = client.post(
                f"/admin/rbac/users/{user_id}/external-identities/protheus/sync",
                json={},
            )

    assert response.status_code == 503


def test_me_protheus_identity_only_self(client, app):
    user_id = uuid4()
    identity = _identity(user_id)

    with app.app_context():
        with client:
            g.current_user = MagicMock(id=user_id, is_superadmin=False, permissions=[])
            with patch(
                "app.interfaces.http.me_controller.SqlAlchemyUnitOfWork"
            ) as mock_uow:
                mock_uow.return_value.__enter__.return_value.protheus_identities.get.return_value = (
                    identity
                )
                # GetUserProtheusIdentityUseCase needs users.get_by_id
                mock_uow.return_value.__enter__.return_value.users.get_by_id.return_value = SimpleNamespace(
                    id=user_id, active=True, email="a@b.com", name="A"
                )
                response = client.get("/me/external-identities/protheus")

    assert response.status_code == 200
    assert response.get_json()["mapping"]["protheus_user_id"] == "000234"


@patch("app.interfaces.http.integrations_protheus_identities_controller.SqlAlchemyUnitOfWork")
def test_s2s_by_protheus_user(mock_uow, client, app, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "s2s-secret")
    user_id = uuid4()
    mock_uow.return_value.__enter__.return_value.protheus_identities.get_by_protheus_user_id.return_value = _identity(
        user_id, protheus_user_id="000234"
    )

    response = client.get(
        "/integrations/protheus-identities/by-protheus-user/000234",
        headers={"X-Delpi-Service-Token": "s2s-secret"},
    )
    assert response.status_code == 200
    assert response.get_json()["mapping"]["user_id"] == str(user_id)


def test_s2s_rejects_missing_token(client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "s2s-secret")
    response = client.get(
        "/integrations/protheus-identities/by-protheus-user/000234",
    )
    assert response.status_code in {401, 403}


def test_leading_zeros_preserved_in_entity_dict():
    user_id = uuid4()
    data = _identity(user_id, protheus_user_id="000234").to_dict()
    assert data["protheus_user_id"] == "000234"
    assert not isinstance(data["protheus_user_id"], int)


@patch("app.interfaces.http.integrations_protheus_identities_controller.SqlAlchemyUnitOfWork")
def test_s2s_write_requires_allowlisted_caller(mock_uow, client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "s2s-secret")
    user_id = uuid4()
    response = client.put(
        f"/integrations/protheus-identities/by-user/{user_id}",
        headers={"X-Delpi-Service-Token": "s2s-secret"},
        json={"protheus_user_id": "000234", "mapping_status": "mapped"},
    )
    assert response.status_code == 403
    mock_uow.assert_not_called()


@patch(
    "app.interfaces.http.integrations_protheus_identities_controller.UpsertUserProtheusIdentityUseCase"
)
@patch("app.interfaces.http.integrations_protheus_identities_controller.SqlAlchemyUnitOfWork")
def test_s2s_write_authorized_with_caller_and_actor(mock_uow, mock_uc, client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "s2s-secret")
    user_id = uuid4()
    actor_id = uuid4()
    mock_uow.return_value.__enter__.return_value.users.get_by_id.return_value = SimpleNamespace(
        id=actor_id, active=True
    )
    mock_uc.return_value.execute.return_value = _identity(user_id).to_dict()

    response = client.put(
        f"/integrations/protheus-identities/by-user/{user_id}",
        headers={
            "X-Delpi-Service-Token": "s2s-secret",
            "X-Delpi-Caller-App": "purchase-requests-api",
        },
        json={
            "protheus_user_id": "000234",
            "mapping_status": "mapped",
            "mapping_source": "manual",
            "verified": True,
            "actor_user_id": str(actor_id),
        },
    )
    assert response.status_code == 200
    kwargs = mock_uc.return_value.execute.call_args.kwargs
    assert kwargs["actor_user_id"] == actor_id


@patch("app.interfaces.http.integrations_protheus_identities_controller.SqlAlchemyUnitOfWork")
def test_s2s_list_paginated(mock_uow, client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "s2s-secret")
    user_id = uuid4()
    mock_uow.return_value.__enter__.return_value.protheus_identities.list_page.return_value = (
        [_identity(user_id)],
        1,
    )
    response = client.get(
        "/integrations/protheus-identities?page=1&page_size=50",
        headers={"X-Delpi-Service-Token": "s2s-secret"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["items"]) == 1
    assert body["pagination"]["total"] == 1
