# app/tests/test_routes_controller.py

from unittest.mock import patch
from flask import g


def test_list_routes_requires_admin(client):
    response = client.get("/admin/apps/crm/routes")
    assert response.status_code in {401, 403}


@patch("app.interfaces.http.apps_controller.ListAppRoutesUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
def test_list_routes_success(mock_uow, mock_uc, client, app, monkeypatch):
    mock_uc.return_value.execute.return_value = type(
        "Result",
        (),
        {"success": True, "routes": [{"path": "/crm"}], "errors": []},
    )()
    mock_uow.return_value.__enter__.return_value = object()
    mock_uow.return_value.__exit__.return_value = False

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {"is_superadmin": True, "permissions": ["apps.view", "apps.manage"]},
        )()
        g.current_permissions = ["apps.view", "apps.manage"]

    response = client.get("/admin/apps/crm/routes")

    assert response.status_code == 200
    assert response.json == [{"path": "/crm"}]
