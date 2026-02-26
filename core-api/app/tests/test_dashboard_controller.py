# app/tests/test_dashboard_controller.py

from unittest.mock import patch
from flask import g


def test_dashboard_requires_auth(client):
    response = client.get("/dashboard/apps")
    assert response.status_code == 401


@patch("app.interfaces.http.dashboard_controller.ListUserAppsUseCase")
@patch("app.interfaces.http.dashboard_controller.SqlAlchemyUnitOfWork")
def test_list_user_apps_success(mock_uow, mock_uc, client, app):
    with app.test_request_context():
        g.current_user = type("User", (), {"id": "123"})()

        mock_uc.return_value.execute.return_value = [{"id": "crm"}]

        response = client.get("/dashboard/apps")

    assert response.status_code == 200
    assert response.json == [{"id": "crm"}]