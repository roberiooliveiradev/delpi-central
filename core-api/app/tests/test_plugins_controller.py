# app/tests/test_plugins_controller.py

from unittest.mock import patch
from flask import g


def test_register_plugin_requires_admin(client):
    response = client.post("/admin/apps/register", json={})
    assert response.status_code in {401, 403}


@patch("app.interfaces.http.apps_controller.RegisterPluginUseCase")
@patch("app.interfaces.http.apps_controller.SqlAlchemyUnitOfWork")
@patch("app.interfaces.http.apps_controller.ManifestValidator")
def test_register_plugin_success(mock_validator, mock_uow, mock_uc, client, app):
    mock_uc.return_value.execute.return_value = type(
        "Result", (), {"success": True, "errors": []}
    )()
    mock_uow.return_value.__enter__.return_value = object()
    mock_uow.return_value.__exit__.return_value = False

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "Admin",
                "is_superadmin": True,
                "permissions": ["apps.manage"],
            },
        )()
        g.current_permissions = ["apps.manage"]

    response = client.post(
        "/admin/apps/register",
        json={"schemaVersion": "1.0.0"},
    )

    assert response.status_code == 201
    assert response.json == {"ok": True}
