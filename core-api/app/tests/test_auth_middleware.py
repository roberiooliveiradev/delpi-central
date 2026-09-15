# app/tests/test_auth_middleware.py

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask, g

import app.interfaces.http.auth_middleware as am


class FakeUsersRepo:
    def __init__(self, existing_user=None):
        self._users_by_id = {}
        self._users_by_email = {}
        self.created = []
        self.identity_updates = []
        self.last_login_updates = []

        if existing_user:
            self._users_by_id[existing_user.id] = existing_user
            self._users_by_email[existing_user.email] = existing_user

    def get_by_id(self, user_id):
        return self._users_by_id.get(user_id)

    def get_by_email(self, email: str):
        return self._users_by_email.get(email)

    def create(self, **kwargs):
        user = SimpleNamespace(
            id=kwargs["id"],
            email=kwargs["email"],
            name=kwargs["name"],
            is_superadmin=kwargs.get("is_superadmin", False),
        )
        self.created.append(user)
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user

    def update_identity(self, user_id, *, name: str, email: str):
        user = self._users_by_id.get(user_id)
        if not user:
            return

        old_email = user.email
        if old_email in self._users_by_email:
            del self._users_by_email[old_email]

        user.name = name
        user.email = email
        self._users_by_email[email] = user
        self.identity_updates.append((user_id, name, email))

    def update_last_login(self, user_id, dt):
        self.last_login_updates.append((user_id, dt))


class FakeRbacQueries:
    def list_role_codes_by_user(self, _user_id):
        return ["role.direct"]

    def list_group_codes_by_user(self, _user_id):
        return ["group.ops"]

    def list_permission_codes_by_user(self, _user_id):
        # Inherited-only query — must NOT be the auth context authority.
        return ["permission.a", "permission.b", "permission.c"]


class FakePermissionQueries:
    def __init__(
        self,
        *,
        all_permissions=None,
        direct=None,
        group=None,
        overrides=None,
    ):
        self._all = all_permissions or []
        self._direct = direct or []
        self._group = group or []
        self._overrides = overrides or []
        self.resolve_calls = 0

    def list_all_permission_codes(self):
        return list(self._all)

    def list_direct_role_permissions(self, _user_id):
        self.resolve_calls += 1
        return list(self._direct)

    def list_group_role_permissions(self, _user_id):
        return list(self._group)

    def list_user_overrides(self, _user_id):
        return list(self._overrides)


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, user_id):
        return self.store.get(user_id)

    def set(self, user_id, permissions):
        self.store[user_id] = permissions

    def invalidate(self, user_id):
        self.store.pop(user_id, None)


class FakeUow:
    def __init__(
        self,
        existing_user=None,
        *,
        permission_queries=None,
        cache=None,
    ):
        self.users = FakeUsersRepo(existing_user=existing_user)
        self.rbac_queries = FakeRbacQueries()
        self.permission_queries = permission_queries or FakePermissionQueries()
        self.cache = cache if cache is not None else FakeCache()
        self.session = self
        self.commits = 0

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture
def app():
    flask_app = Flask("test_auth_middleware")
    flask_app.config["TESTING"] = True
    return flask_app


def _auth_headers():
    return {"Authorization": "Bearer token"}


def test_authenticate_missing_header_returns_none(app, monkeypatch):
    with app.test_request_context("/any", headers={}):
        assert am.authenticate() is None
        assert not hasattr(g, "current_user")


def test_authenticate_syncs_name_and_email_on_login(app, monkeypatch):
    user_id = uuid4()
    existing = SimpleNamespace(
        id=user_id,
        email="old@test.com",
        name="Nome Antigo",
        is_superadmin=False,
    )

    monkeypatch.setattr(
        am,
        "validate_token",
        lambda _t: {
            "sub": str(user_id),
            "email": "new@test.com",
            "name": "Nome Novo",
        },
    )

    uow = FakeUow(existing_user=existing)
    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)
    monkeypatch.setattr(am, "SendWelcomeNotificationUseCase", lambda _uow: object())

    with app.test_request_context("/any", headers=_auth_headers()):
        assert am.authenticate() is None
        assert g.current_user.email == "new@test.com"
        assert g.current_user.name == "Nome Novo"
        assert len(uow.users.identity_updates) == 1
        assert len(uow.users.last_login_updates) == 1


def test_authenticate_new_user_creates_without_identity_sync(app, monkeypatch):
    user_id = uuid4()

    monkeypatch.setattr(
        am,
        "validate_token",
        lambda _t: {
            "sub": str(user_id),
            "email": "new@test.com",
            "name": "Novo Usuário",
        },
    )

    uow = FakeUow(existing_user=None)
    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)

    notified = {"called": False}

    class FakeWelcome:
        def __init__(self, _uow):
            pass

        def execute(self, _user_id):
            notified["called"] = True

    monkeypatch.setattr(am, "SendWelcomeNotificationUseCase", FakeWelcome)

    with app.test_request_context("/any", headers=_auth_headers()):
        assert am.authenticate() is None
        assert len(uow.users.created) == 1
        assert uow.users.created[0].email == "new@test.com"
        assert notified["called"] is True
        assert len(uow.users.identity_updates) == 0


def test_authenticate_skips_jwt_for_integrations_service_token(app, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "service-token-secret")

    with app.test_request_context(
        "/integrations/directory/users",
        headers={"Authorization": "Bearer service-token-secret"},
    ):
        assert am.authenticate() is None
        assert not hasattr(g, "current_user")


def test_is_effective_access_service_path_only_owned_surface():
    assert am._is_effective_access_service_path(
        f"/integrations/effective-access/subjects/{uuid4()}"
    )
    assert am._is_effective_access_service_path(
        f"/apps/core-api/integrations/effective-access/subjects/{uuid4()}"
    )
    assert am._is_effective_access_service_path(
        f"/integrations/effective-access/subjects/{uuid4()}/"
    )
    assert not am._is_effective_access_service_path("/integrations/effective-access")
    assert not am._is_effective_access_service_path(
        "/integrations/effective-access/subjects/"
    )
    assert not am._is_effective_access_service_path(
        f"/integrations/effective-access/subjects/{uuid4()}/extra"
    )
    assert not am._is_effective_access_service_path("/integrations/directory/users")
    assert not am._is_effective_access_service_path("/me")
    assert not am._is_effective_access_service_path("/admin/statistics")
    assert not am._is_effective_access_service_path("/integrations/")


def test_authenticate_skips_jwt_for_effective_access_token_only_on_owned_path(
    app, monkeypatch
):
    secret = "effective-access-secret"
    monkeypatch.setenv("CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN", secret)
    called = {"validate": 0}

    def _fail_validate(_token):
        called["validate"] += 1
        raise ValueError("should not validate jwt for owned path")

    monkeypatch.setattr(am, "validate_token", _fail_validate)

    with app.test_request_context(
        f"/integrations/effective-access/subjects/{uuid4()}",
        headers={"Authorization": f"Bearer {secret}"},
    ):
        assert am.authenticate() is None
        assert not hasattr(g, "current_user")
        assert called["validate"] == 0


def test_authenticate_rejects_effective_access_token_on_me(app, monkeypatch):
    secret = "effective-access-secret"
    monkeypatch.setenv("CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN", secret)

    with app.test_request_context(
        "/me",
        headers={"Authorization": f"Bearer {secret}"},
    ):
        result = am.authenticate()
        assert result is not None
        body, status = result
        assert status == 401
        assert body.get_json()["errors"][0]["code"] == "invalid_token"
        assert not hasattr(g, "current_user")


def test_authenticate_rejects_effective_access_token_on_admin_route(app, monkeypatch):
    secret = "effective-access-secret"
    monkeypatch.setenv("CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN", secret)

    with app.test_request_context(
        "/admin/statistics",
        headers={"Authorization": f"Bearer {secret}"},
    ):
        result = am.authenticate()
        assert result is not None
        _, status = result
        assert status == 401
        assert not hasattr(g, "current_user")


def test_authenticate_rejects_effective_access_token_on_unrelated_integration(
    app, monkeypatch
):
    secret = "effective-access-secret"
    monkeypatch.setenv("CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN", secret)
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "integrations-shared-secret")

    with app.test_request_context(
        "/integrations/notifications",
        headers={"Authorization": f"Bearer {secret}"},
    ):
        result = am.authenticate()
        assert result is not None
        _, status = result
        assert status == 401
        assert not hasattr(g, "current_user")


def test_authenticate_sets_effective_permissions_via_permission_resolver(
    app, monkeypatch
):
    user_id = uuid4()
    existing = SimpleNamespace(
        id=user_id,
        email="user@test.com",
        name="User",
        is_superadmin=False,
    )

    monkeypatch.setattr(
        am,
        "validate_token",
        lambda _t: {
            "sub": str(user_id),
            "email": "user@test.com",
            "name": "User",
        },
    )

    permission_queries = FakePermissionQueries(
        direct=["permission.a", "permission.b"],
        group=["permission.c"],
        overrides=[("permission.b", False), ("permission.d", True)],
    )
    uow = FakeUow(existing_user=existing, permission_queries=permission_queries)
    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)

    with app.test_request_context("/any", headers=_auth_headers()):
        assert am.authenticate() is None

        # Inherited-only would be a/b/c; effective must drop b and add d.
        assert sorted(g.current_user.permissions) == [
            "permission.a",
            "permission.c",
            "permission.d",
        ]
        assert g.current_user.roles == ["role.direct"]
        assert g.current_user.groups == ["group.ops"]
        assert g.current_user.is_superadmin is False
        assert permission_queries.resolve_calls >= 1


def test_authenticate_superadmin_gets_all_registered_permission_codes(
    app, monkeypatch
):
    user_id = uuid4()
    existing = SimpleNamespace(
        id=user_id,
        email="admin@test.com",
        name="Admin",
        is_superadmin=True,
    )

    monkeypatch.setattr(
        am,
        "validate_token",
        lambda _t: {
            "sub": str(user_id),
            "email": "admin@test.com",
            "name": "Admin",
        },
    )

    permission_queries = FakePermissionQueries(
        all_permissions=["permission.a", "permission.z", "rbac.manage"],
        direct=["permission.a"],
        group=[],
        overrides=[],
    )
    uow = FakeUow(existing_user=existing, permission_queries=permission_queries)
    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)

    with app.test_request_context("/any", headers=_auth_headers()):
        assert am.authenticate() is None
        assert sorted(g.current_user.permissions) == [
            "permission.a",
            "permission.z",
            "rbac.manage",
        ]
        assert g.current_user.is_superadmin is True
