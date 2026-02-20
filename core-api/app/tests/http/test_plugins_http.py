# app/tests/http/test_plugins_http.py

def test_register_plugin_http(client, superadmin_user):

    manifest = {
        "schemaVersion": "2.0.0",
        "id": "crm",
        "name": "CRM",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/crm",
        "entry": "/apps/crm/remoteEntry.js",
        "permissions": [
            {"code": "crm.access", "description": "Acesso", "module": "crm"}
        ],
        "routes": [
            {"path": "/crm", "label": "CRM", "permission": "crm.access"}
        ],
    }

    response = client.post(
        "/core-api/plugins/register",
        json=manifest,
    )

    assert response.status_code == 201
    assert response.json["appId"] == "crm"