# app/tests/http/test_apps_admin_management.py

import json
from pathlib import Path


import uuid

def register_finance_plugin(client):
    import random
    import string

    suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    module = f"finance{suffix}"

    permission_code = f"{module}.dashboard.read"

    manifest = {
        "schemaVersion": "2.0.0",
        "id": module,
        "name": "Financeiro",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": f"/{module}",
        "entry": "/apps/finance/remoteEntry.js",
        "permissions": [
            {
                "code": permission_code,
                "name": "Access dashboard",
                "description": "Access finance dashboard",
                "module": module,
            }
        ],
        "routes": [
            {
                "path": f"/{module}",
                "label": "Finance",
                "permission": permission_code,
            }
        ],
    }

    return client.post("/core-api/plugins/register", json=manifest)


def test_apps_admin_update_and_bulk(client, superadmin_user):

    # 1️⃣ Criar via plugin
    resp = register_finance_plugin(client)
    print(resp.json)
    assert resp.status_code == 201

    app_id = resp.json["appId"]

    # 2️⃣ Atualizar app
    resp = client.put(
        f"/core-api/admin/apps/{app_id}",
        json={"description": "Nova descrição"}
    )
    assert resp.status_code == 200

    # 3️⃣ Bulk deactivate
    resp = client.post(
        "/core-api/admin/apps/bulk-deactivate",
        json={"ids": [app_id]}
    )
    assert resp.status_code == 200

    # 4️⃣ Bulk activate
    resp = client.post(
        "/core-api/admin/apps/bulk-activate",
        json={"ids": [app_id]}
    )
    assert resp.status_code == 200

    # 5️⃣ List apps
    resp = client.get("/core-api/admin/apps")
    assert resp.status_code == 200
    assert any(a["id"] == app_id for a in resp.json["data"])
