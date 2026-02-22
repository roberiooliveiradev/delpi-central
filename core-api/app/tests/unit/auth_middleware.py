# app/tests/unit/test_auth_middleware.py

import uuid
import pytest
from flask import g

from app.extensions.db import db
from app.infrastructure.db.models import User


def test_authenticate_returns_none_when_no_header(app):
    from app.interfaces.http.auth_middleware import authenticate

    with app.test_request_context("/any", headers={}):
        user = authenticate()
        assert user is None
        assert getattr(g, "current_user", None) is None


def test_authenticate_creates_user_and_sets_g_on_cache_miss(app, monkeypatch):
    """
    Caminhos cobertos:
    - header Bearer ok
    - user não existe -> cria user
    - is_new_user True -> chama notify_user
    - cache miss -> resolve_user_permissions + rbac_cache.set
    - seta g.current_user, g.current_permissions, g.current_sub
    """
    from app.interfaces.http import auth_middleware

    sub = str(uuid.uuid4())
    claims = {"sub": sub, "email": "new@test.com", "name": "New User"}

    # token -> claims
    monkeypatch.setattr(auth_middleware.jwt_service, "verify_token", lambda token: claims)

    # notify_user spy
    called = {"notify": False}
    def fake_notify_user(**kwargs):
        called["notify"] = True
        assert kwargs["sub"] == sub
        assert kwargs["type"] == "success"
    monkeypatch.setattr(auth_middleware, "notify_user", fake_notify_user)

    # cache miss
    monkeypatch.setattr(auth_middleware.rbac_cache, "get", lambda key: None)

    # resolver + cache.set
    monkeypatch.setattr(auth_middleware, "resolve_user_permissions", lambda user: ["a.view", "b.view"])
    set_called = {"ok": False}
    def fake_set(key, value):
        set_called["ok"] = True
        assert key == sub
        assert value == ["a.view", "b.view"]
    monkeypatch.setattr(auth_middleware.rbac_cache, "set", fake_set)

    with app.test_request_context("/x", headers={"Authorization": "Bearer fake-token"}):
        user = auth_middleware.authenticate()

        assert user is not None
        assert user.email == "new@test.com"
        assert user.id == sub  # id = sub
        assert called["notify"] is True
        assert set_called["ok"] is True

        assert g.current_user.email == "new@test.com"
        assert g.current_permissions == ["a.view", "b.view"]
        assert g.current_sub == sub

    # confirma persistência
    with app.app_context():
        u = User.query.filter_by(email="new@test.com").first()
        assert u is not None
        assert str(u.id) == sub
        assert u.last_login_at is not None


def test_authenticate_existing_user_cache_hit_does_not_resolve(app, monkeypatch):
    """
    Caminhos cobertos:
    - user existe
    - cache hit -> NÃO chama resolve_user_permissions nem rbac_cache.set
    - NÃO chama notify_user
    """
    from app.interfaces.http import auth_middleware

    user_id = str(uuid.uuid4())
    with app.app_context():
        u = User(id=user_id, email="exists@test.com", name="Exists")
        db.session.add(u)
        db.session.commit()

    claims = {"sub": user_id, "email": "exists@test.com", "name": "Exists"}
    monkeypatch.setattr(auth_middleware.jwt_service, "verify_token", lambda token: claims)

    # cache hit
    monkeypatch.setattr(auth_middleware.rbac_cache, "get", lambda key: ["cached.permission"])

    # garantir que não foi chamado
    monkeypatch.setattr(auth_middleware, "resolve_user_permissions", lambda user: (_ for _ in ()).throw(AssertionError("should not resolve")))
    monkeypatch.setattr(auth_middleware.rbac_cache, "set", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not set cache")))
    monkeypatch.setattr(auth_middleware, "notify_user", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not notify")))

    with app.test_request_context("/x", headers={"Authorization": "Bearer fake-token"}):
        user = auth_middleware.authenticate()

        assert user.email == "exists@test.com"
        assert g.current_permissions == ["cached.permission"]
        assert g.current_sub == user_id
        assert g.current_user.email == "exists@test.com"