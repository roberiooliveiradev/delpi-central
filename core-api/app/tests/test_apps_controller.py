# app/tests/test_apps_controller.py

from unittest.mock import MagicMock, patch

import pytest
from flask import g

from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_list_apps_requires_auth(client):
    response = client.get("/admin/apps")
    assert response.status_code == 401


@patch("app.interfaces.http.apps_controller.ListAdminAppsUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
def test_list_apps_success(mock_uow, mock_uc, client, app):
    app_dto = MagicMock()
    app_dto.__dict__ = {
        "id": "crm",
        "name": "CRM",
        "type": "microfrontend",
    }
    mock_uc.return_value.execute.return_value = ([app_dto], 1)

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get("/admin/apps")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"] == [{"id": "crm", "name": "CRM", "type": "microfrontend"}]
    assert payload["pagination"]["total"] == 1


@patch("app.interfaces.http.apps_controller.ListAdminAppsUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
def test_list_apps_passes_type_filter(mock_uow, mock_uc, client, app):
    mock_uc.return_value.execute.return_value = ([], 0)

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get("/admin/apps?type=microfrontend")

    assert response.status_code == 200
    mock_uc.return_value.execute.assert_called_once()
    assert mock_uc.return_value.execute.call_args.kwargs["app_type"] == "microfrontend"


@patch("app.interfaces.http.apps_controller.ListAdminAppsUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
def test_list_apps_invalid_type_returns_400(mock_uow, mock_uc, client, app):
    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get("/admin/apps?type=invalid")

    assert response.status_code == 400
    mock_uc.return_value.execute.assert_not_called()
