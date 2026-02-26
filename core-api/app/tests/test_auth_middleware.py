# app/tests/test_auth_middleware.py

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask, g

import app.interfaces.http.auth_middleware as am


class FakeUsersRepo:
    def __init__(self, existing_user=None):
        self._user = existing_user
        self.created = []
        self.last_login_updates = []

    def get_by_email(self, email: str):
        return self._user

    def create(self, **kwargs):
        # cria e deixa disponível no get_by_email
        user = SimpleNamespace(
            id=kwargs["id"],
            email=kwargs["email"],
            name=kwargs["name"],
            is_superadmin=kwargs.get("is_superadmin", False),
        )
        self.created.append(user)
        self._user = user

    def update_last_login(self, user_id, dt):
        self.last_login_updates.append((user_id, dt))


class FakePermissionQueries:
    pass


class FakeUow:
    def __init__(self, existing_user=None):
        self.users = FakeUsersRepo(existing_user=existing_user)
        self.permission_queries = FakePermissionQueries()
        self.commits = 0

    def commit(self):
        self.commits += 1


@pytest.fixture
def app():
    app = Flask("test_auth_middleware")
    app.config["TESTING"] = True
    return app


def _set_auth_header(client, token: str):
    return {"Authorization": f"Bearer {token}"}


def test_authenticate_missing_header_returns_none(app, monkeypatch):
    with app.test_request_context("/any", headers={}):
        user = am.authenticate()
        assert user is None
        assert not hasattr(g, "current_user")


def test_authenticate_invalid_token_returns_none(app, monkeypatch):
    def boom(_token):
        raise Exception("invalid")

    monkeypatch.setattr(am.jwt_service, "verify_token", boom)

    with app.test_request_context("/any", headers=_set_auth_header(None, "x")):
        user = am.authenticate()
        assert user is None
        assert not hasattr(g, "current_user")


def test_authenticate_sub_not_uuid_returns_none(app, monkeypatch):
    monkeypatch.setattr(
        am.jwt_service,
        "verify_token",
        lambda _t: {"sub": "not-a-uuid", "email": "u@test.com", "name": "User"},
    )

    with app.test_request_context("/any", headers=_set_auth_header(None, "x")):
        user = am.authenticate()
        assert user is None
        assert not hasattr(g, "current_user")


def test_authenticate_existing_user_sets_g_context(app, monkeypatch):
    user_id = uuid4()
    existing = SimpleNamespace(
        id=user_id,
        email="u@test.com",
        name="User",
        is_superadmin=False,
    )

    # claims ok
    monkeypatch.setattr(
        am.jwt_service,
        "verify_token",
        lambda _t: {"sub": str(user_id), "email": "u@test.com", "name": "User"},
    )

    # UoW
    uow = FakeUow(existing_user=existing)

    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)

    # PermissionResolver.resolve
    class FakeResolver:
        def __init__(self, permission_query, cache):
            self.permission_query = permission_query
            self.cache = cache

        def resolve(self, user_id, is_superadmin):
            assert user_id == existing.id
            assert is_superadmin is False
            return ["apps.manage", "dashboard.view"]

    monkeypatch.setattr(am, "PermissionResolver", FakeResolver)

    with app.test_request_context("/any", headers=_set_auth_header(None, "x")):
        user = am.authenticate()

        assert user is existing
        assert g.current_user is existing
        assert g.current_sub == str(existing.id)
        assert g.current_permissions == ["apps.manage", "dashboard.view"]

        # update_last_login + commit chamados
        assert len(uow.users.last_login_updates) == 1
        assert uow.commits >= 1


def test_authenticate_new_user_creates_and_notifies(app, monkeypatch):
    user_id = uuid4()

    monkeypatch.setattr(
        am.jwt_service,
        "verify_token",
        lambda _t: {"sub": str(user_id), "email": "new@test.com", "name": "New User"},
    )

    uow = FakeUow(existing_user=None)
    monkeypatch.setattr(am, "SqlAlchemyUnitOfWork", lambda: uow)

    notified = {"called": False, "args": None}

    class FakeNotifyUC:
        def __init__(self, _uow):
            self.uow = _uow

        def execute(self, **kwargs):
            notified["called"] = True
            notified["args"] = kwargs

    monkeypatch.setattr(am, "NotifyUserUseCase", FakeNotifyUC)

    class FakeResolver:
        def __init__(self, permission_query, cache):
            self.permission_query = permission_query
            self.cache = cache

        def resolve(self, user_id, is_superadmin):
            return ["dashboard.view"]

    monkeypatch.setattr(am, "PermissionResolver", FakeResolver)

    with app.test_request_context("/any", headers=_set_auth_header(None, "x")):
        user = am.authenticate()

        assert user is not None
        assert user.email == "new@test.com"
        assert len(uow.users.created) == 1  # criou usuário
        assert notified["called"] is True  # notificou boas-vindas
        assert "Bem-vindo" in notified["args"]["title"]

        assert g.current_user.email == "new@test.com"
        assert g.current_permissions == ["dashboard.view"]