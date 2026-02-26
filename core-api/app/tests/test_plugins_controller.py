# app/tests/test_plugins_controller.py

from unittest.mock import patch
from flask import g


def test_register_plugin_requires_admin(client):
    response = client.post("/admin/plugins/register", json={})
    assert response.status_code == 401


@patch("app.interfaces.http.plugins_controller.RegisterPluginUseCase")
@patch("app.interfaces.http.plugins_controller.SqlAlchemyUnitOfWork")
@patch("app.interfaces.http.plugins_controller.ManifestValidator")
def test_register_plugin_success(mock_validator, mock_uow, mock_uc, client, app):
    with app.test_request_context():
        g.current_user = type("User", (), {"is_superadmin": True})()

        mock_uc.return_value.execute.return_value = type(
            "Result", (), {"success": True, "errors": []}
        )()

        response = client.post(
            "/admin/plugins/register",
            json={"schemaVersion": "2.0.0"},
        )

    assert response.status_code == 201
    assert response.json == {"ok": True}