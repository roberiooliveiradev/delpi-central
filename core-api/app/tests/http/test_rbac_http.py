# app/tests/http/test_rbac_http.py

def test_list_permissions_requires_rbac_manage(client, superadmin_user):
    response = client.get("/core-api/admin/rbac/permissions")

    # superadmin bypass → deve retornar 200
    assert response.status_code == 200