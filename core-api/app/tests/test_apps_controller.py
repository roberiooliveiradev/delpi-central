# app/tests/test_apps_controller.py

from unittest.mock import patch
from flask import g


def test_list_apps_requires_auth(client):
    response = client.get("/admin/apps")
    assert response.status_code == 401


@patch("app.interfaces.http.apps_controller.ListAdminAppsUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
def test_list_apps_success(mock_uow, mock_uc, client, app):
    with app.test_request_context():
        g.current_user = object()

        mock_uc.return_value.execute.return_value = [
            type("App", (), {"__dict__": {"id": "crm"}})()
        ]

        response = client.get("/admin/apps")

    assert response.status_code == 200
    assert response.json == [{"id": "crm"}]