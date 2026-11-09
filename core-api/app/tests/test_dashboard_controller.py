# app/tests/test_dashboard_controller.py
# Dashboard apps surface moved to /me/apps (me_controller).

from unittest.mock import patch
from flask import g
from uuid import uuid4


def test_dashboard_requires_auth(client):
    response = client.get("/me/apps")
    assert response.status_code == 401


@patch("app.interfaces.http.me_controller.ListUserAppsUseCase")
@patch("app.interfaces.http.me_controller.SqlAlchemyUnitOfWork")
def test_list_user_apps_success(mock_uow, mock_uc, client, app):
    from types import SimpleNamespace

    mock_uc.return_value.execute.return_value = [{"id": "crm"}]
    mock_uow.return_value.__enter__.return_value = SimpleNamespace(
        app_queries=object()
    )
    mock_uow.return_value.__exit__.return_value = False

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {
                "id": str(uuid4()),
                "permissions": [],
                "is_superadmin": False,
            },
        )()
        g.current_permissions = []

    response = client.get("/me/apps")

    assert response.status_code == 200
    assert response.json == [{"id": "crm"}]
