# app/tests/conftest.py

import pytest
from app.create_app import create_app
from app.extensions.db import db


# ==========================================================
# APP
# ==========================================================

@pytest.fixture(scope="function")
def app():

    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ==========================================================
# SESSION
# ==========================================================

@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        yield db.session
        
# ==========================================================
# CLIENT
# ==========================================================

@pytest.fixture
def client(app):
    return app.test_client()


# ==========================================================
# SUPERADMIN USER
# ==========================================================

@pytest.fixture
def superadmin_user(app):
    from app.infrastructure.db.models import User

    with app.app_context():
        user = User(
            id="11111111-1111-1111-1111-111111111111",
            email="admin@test.com",
            name="Admin Test",
            is_superadmin=True
        )
        db.session.add(user)
        # O commit expira os atributos por padrão
        db.session.commit()
        
        # Opção A: Refresh para garantir que os dados fiquem no objeto
        db.session.refresh(user) 
        
        # Opção B (Alternativa): Tornar o objeto persistente fora da sessão
        db.session.expunge(user) 

        return user


# ==========================================================
# AUTH HEADERS (MOCK JWT)
# ==========================================================

@pytest.fixture
def auth_headers(monkeypatch):

    from app.interfaces.http.auth_middleware import jwt_service

    def fake_verify_token(token):
        return {
            "sub": "11111111-1111-1111-1111-111111111111",
            "email": "admin@test.com",
            "name": "Admin Test"
        }

    monkeypatch.setattr(jwt_service, "verify_token", fake_verify_token)

    return {
        "Authorization": "Bearer fake-token"
    }