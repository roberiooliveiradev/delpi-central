# app/tests/test_routes_controller.py

from unittest.mock import patch
from flask import g


def test_list_routes_requires_admin(client):
    response = client.get("/admin/apps/crm/routes")
    assert response.status_code == 401


@patch("app.interfaces.http.routes_controller.ListAppRoutesUseCase")
@patch("app.interfaces.http.routes_controller.SqlAlchemyUnitOfWork")
def test_list_routes_success(mock_uow, mock_uc, client, app):
    with app.test_request_context():
        g.current_user = type("User", (), {"is_superadmin": True})()

        mock_uc.return_value.execute.return_value = type(
            "Result",
            (),
            {"success": True, "routes": [{"path": "/crm"}], "errors": []},
        )()

        response = client.get("/admin/apps/crm/routes")

    assert response.status_code == 200
    assert response.json == [{"path": "/crm"}]