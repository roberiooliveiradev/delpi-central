# app/tests/http/test_apps_admin_full_flow.py

def test_apps_admin_full_flow(client, superadmin_user):

    # -------------------------------------------------
    # 1️⃣ Criar app
    # -------------------------------------------------
    resp = client.post(
        "/core-api/admin/apps",
        json={
            "id": "finance",
            "name": "Financeiro",
            "base_path": "/finance",
            "type": "microfrontend"
        }
    )
    assert resp.status_code == 201

    # -------------------------------------------------
    # 2️⃣ Atualizar app
    # -------------------------------------------------
    resp = client.put(
        "/core-api/admin/apps/finance",
        json={"version": "1.1.0"}
    )
    assert resp.status_code == 200

    # -------------------------------------------------
    # 3️⃣ Desativar
    # -------------------------------------------------
    resp = client.post("/core-api/admin/apps/finance/deactivate")
    assert resp.status_code == 200

    # -------------------------------------------------
    # 4️⃣ Ativar
    # -------------------------------------------------
    resp = client.post("/core-api/admin/apps/finance/activate")
    assert resp.status_code == 200

    # -------------------------------------------------
    # 5️⃣ Criar rota
    # -------------------------------------------------
    resp = client.post(
        "/core-api/admin/apps/finance/routes",
        json={"path": "/finance/home"}
    )
    assert resp.status_code == 201
    route_id = resp.json["id"]

    # -------------------------------------------------
    # 6️⃣ Atualizar rota
    # -------------------------------------------------
    resp = client.put(
        f"/core-api/admin/apps/routes/{route_id}",
        json={"path": "/finance/dashboard"}
    )
    assert resp.status_code == 200