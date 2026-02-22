# app/tests/http/test_apps_admin_errors.py

def test_create_app_missing_fields(client, superadmin_user):
    resp = client.post(
        "/core-api/admin/apps",
        json={"id": "x"}
    )
    assert resp.status_code == 400


def test_create_app_conflict(client, superadmin_user):
    payload = {
        "id": "app1",
        "name": "App1",
        "base_path": "/a1",
        "type": "microfrontend"
    }

    client.post("/core-api/admin/apps", json=payload)
    resp = client.post("/core-api/admin/apps", json=payload)

    assert resp.status_code == 409