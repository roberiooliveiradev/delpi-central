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
        return []

    def list_group_codes_by_user(self, _user_id):
        return []

    def list_permission_codes_by_user(self, _user_id):
        return []


class FakeUow:
    def __init__(self, existing_user=None):
        self.users = FakeUsersRepo(existing_user=existing_user)
        self.rbac_queries = FakeRbacQueries()
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
