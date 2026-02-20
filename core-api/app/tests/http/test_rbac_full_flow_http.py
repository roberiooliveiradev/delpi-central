# app/tests/http/test_rbac_full_flow_http.py

def test_rbac_full_flow(client, superadmin_user):

    user_id = str(superadmin_user.id)

    # 1️⃣ Criar permission
    resp = client.post(
        "/core-api/admin/rbac/permissions",
        json={
            "code": "reports.view",
            "name": "Visualizar relatórios"
        }
    )
    assert resp.status_code == 201
    permission_id = resp.json["id"]

    # 2️⃣ Criar role
    resp = client.post(
        "/core-api/admin/rbac/roles",
        json={"name": "Analyst"}
    )
    assert resp.status_code == 201
    role_id = resp.json["id"]

    # 3️⃣ Vincular permission à role
    resp = client.put(
        f"/core-api/admin/rbac/roles/{role_id}/permissions",
        json={"permissionIds": [permission_id]}
    )
    assert resp.status_code == 200

    # 4️⃣ Vincular role ao usuário
    resp = client.put(
        f"/core-api/admin/rbac/users/{user_id}/roles",
        json={"roleIds": [role_id]}
    )
    assert resp.status_code == 200

    # 5️⃣ Confirmar
    resp = client.get(f"/core-api/admin/rbac/users/{user_id}")
    assert resp.status_code == 200
    assert len(resp.json["roles"]) == 1