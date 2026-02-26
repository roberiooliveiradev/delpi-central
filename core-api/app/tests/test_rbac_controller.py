# app/tests/test_rbac_controller.py

import pytest
from types import SimpleNamespace


@pytest.fixture(autouse=True)
def mock_auth(app):
    @app.before_request
    def inject_user():
        from flask import g
        g.current_user = SimpleNamespace(id="user1")
    yield


@pytest.fixture
def mock_uow(monkeypatch):
    class FakeUow:
        def rollback(self):
            pass

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork",
        lambda: FakeUow()
    )


def test_create_role_validation_error(client):
    response = client.post("/admin/roles", json={})
    assert response.status_code == 400


def test_create_role_success(client, monkeypatch):
    class FakeUC:
        def __init__(self, uow):
            pass

        def execute(self, name, description=None):
            return "role-id-123"

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.CreateRoleUseCase",
        FakeUC
    )

    response = client.post("/admin/roles", json={"name": "Admin"})
    assert response.status_code == 201


def test_list_role_permissions(client, monkeypatch):
    class FakeUC:
        def __init__(self, uow):
            pass

        def execute(self, role_id):
            return []

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.ListRolePermissionsUseCase",
        FakeUC
    )

    response = client.get("/admin/roles/1/permissions")
    assert response.status_code == 200


def test_replace_role_permissions_validation_error(client):
    response = client.put("/admin/roles/1/permissions", json={})
    assert response.status_code == 400