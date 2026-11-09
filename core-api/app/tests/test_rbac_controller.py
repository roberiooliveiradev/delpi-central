# app/tests/test_rbac_controller.py

import pytest
from types import SimpleNamespace


@pytest.fixture(autouse=True)
def mock_auth(app):
    @app.before_request
    def inject_user():
        from flask import g
        g.current_user = SimpleNamespace(
            id="user1",
            is_superadmin=True,
            permissions=["rbac.manage", "roles.manage"],
        )
        g.current_permissions = ["rbac.manage", "roles.manage"]
    yield


def test_create_role_validation_error(client, monkeypatch):
    class FakeUC:
        def __init__(self, uow):
            pass

        def execute(self, name, description=None):
            raise ValueError("name required")

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.CreateRoleUseCase",
        FakeUC,
    )
    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork",
        lambda: SimpleNamespace(__enter__=lambda s: s, __exit__=lambda *a: False),
    )

    response = client.post("/admin/rbac/roles", json={})
    assert response.status_code in {400, 422}


def test_create_role_success(client, monkeypatch):
    class FakeUC:
        def __init__(self, uow):
            pass

        def execute(self, name, description=None):
            return "role-id-123"

    class FakeUow:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self):
            pass

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.CreateRoleUseCase",
        FakeUC,
    )
    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork",
        FakeUow,
    )

    response = client.post("/admin/rbac/roles", json={"name": "Admin"})
    assert response.status_code == 201


def test_list_role_permissions(client, monkeypatch):
    class FakeUC:
        def __init__(self, uow):
            pass

        def execute(self, role_id):
            return []

    class FakeUow:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.ListRolePermissionsUseCase",
        FakeUC,
    )
    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork",
        FakeUow,
    )

    response = client.get("/admin/rbac/roles/1/permissions")
    assert response.status_code == 200


def test_replace_role_permissions_validation_error(client, monkeypatch):
    class FakeUow:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork",
        FakeUow,
    )
    response = client.put("/admin/rbac/roles/1/permissions", json={})
    assert response.status_code in {400, 422}
