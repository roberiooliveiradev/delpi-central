# app/tests/http/test_rbac_negative_cases.py

def test_delete_permission(client, superadmin_user):
    resp = client.post(
        "/core-api/admin/rbac/permissions",
        json={"code": "x.test", "name": "X"}
    )
    pid = resp.json["id"]

    resp = client.delete(f"/core-api/admin/rbac/permissions/{pid}")
    assert resp.status_code == 200


def test_delete_role(client, superadmin_user):
    resp = client.post(
        "/core-api/admin/rbac/roles",
        json={"name": "TempRole"}
    )
    rid = resp.json["id"]

    resp = client.delete(f"/core-api/admin/rbac/roles/{rid}")
    assert resp.status_code == 200


def test_permission_conflict(client, superadmin_user):
    client.post(
        "/core-api/admin/rbac/permissions",
        json={"code": "dup.test", "name": "Dup"}
    )

    resp = client.post(
        "/core-api/admin/rbac/permissions",
        json={"code": "dup.test", "name": "Dup2"}
    )

    assert resp.status_code == 409