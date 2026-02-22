# app/tests/http/test_rbac_more_coverage_http.py

def test_rbac_lists_and_filters(client, superadmin_user):
    # cria permissions
    client.post("/core-api/admin/rbac/permissions", json={"code": "p.a", "name": "PA"})
    client.post("/core-api/admin/rbac/permissions", json={"code": "p.b", "name": "PB"})

    # lista permissions
    resp = client.get("/core-api/admin/rbac/permissions")
    assert resp.status_code == 200
    assert any(p["code"] == "p.a" for p in resp.json)

    # cria role
    resp = client.post("/core-api/admin/rbac/roles", json={"name": "Role1"})
    assert resp.status_code == 201

    # lista roles
    resp = client.get("/core-api/admin/rbac/roles")
    assert resp.status_code == 200
    assert any(r["name"] == "Role1" for r in resp.json)

    # cria group
    resp = client.post("/core-api/admin/rbac/groups", json={"name": "Group1"})
    assert resp.status_code == 201

    # lista groups
    resp = client.get("/core-api/admin/rbac/groups")
    assert resp.status_code == 200
    assert any(g["name"] == "Group1" for g in resp.json)

    # lista users + filtro q
    resp = client.get("/core-api/admin/rbac/users?q=admin@test.com")
    assert resp.status_code == 200
    assert any(u["email"] == "admin@test.com" for u in resp.json)


def test_rbac_permission_bad_requests_and_not_found(client, superadmin_user):
    # missing fields -> 400
    resp = client.post("/core-api/admin/rbac/permissions", json={"code": ""})
    assert resp.status_code == 400

    # create ok
    resp = client.post("/core-api/admin/rbac/permissions", json={"code": "dup.x", "name": "X"})
    assert resp.status_code == 201
    pid = resp.json["id"]

    # conflict -> 409
    resp = client.post("/core-api/admin/rbac/permissions", json={"code": "dup.x", "name": "X2"})
    assert resp.status_code == 409

    # update not found -> 404
    resp = client.put("/core-api/admin/rbac/permissions/00000000-0000-0000-0000-000000000000",
                      json={"name": "NO"})
    assert resp.status_code == 404

    # update ok
    resp = client.put(f"/core-api/admin/rbac/permissions/{pid}",
                      json={"name": "X Updated", "description": "desc"})
    assert resp.status_code == 200
    assert resp.json["name"] == "X Updated"


def test_rbac_roles_bad_requests_and_conflict(client, superadmin_user):
    # missing -> 400
    resp = client.post("/core-api/admin/rbac/roles", json={})
    assert resp.status_code == 400

    # create ok
    resp = client.post("/core-api/admin/rbac/roles", json={"name": "RoleDup"})
    assert resp.status_code == 201
    rid = resp.json["id"]

    # conflict -> 409
    resp = client.post("/core-api/admin/rbac/roles", json={"name": "RoleDup"})
    assert resp.status_code == 409

    # update not found -> 404
    resp = client.put("/core-api/admin/rbac/roles/00000000-0000-0000-0000-000000000000",
                      json={"name": "X"})
    assert resp.status_code == 404

    # update ok
    resp = client.put(f"/core-api/admin/rbac/roles/{rid}", json={"description": "desc"})
    assert resp.status_code == 200
    assert resp.json["description"] == "desc"

    # set_role_permissions wrong type -> 400
    resp = client.put(f"/core-api/admin/rbac/roles/{rid}/permissions", json={"permissionIds": "nope"})
    assert resp.status_code == 400


def test_rbac_groups_bad_requests_and_not_found(client, superadmin_user):
    # missing name -> 400
    resp = client.post("/core-api/admin/rbac/groups", json={})
    assert resp.status_code == 400

    # create ok
    resp = client.post("/core-api/admin/rbac/groups", json={"name": "Gdup"})
    assert resp.status_code == 201
    gid = resp.json["id"]

    # conflict -> 409
    resp = client.post("/core-api/admin/rbac/groups", json={"name": "Gdup"})
    assert resp.status_code == 409

    # update not found -> 404
    resp = client.put("/core-api/admin/rbac/groups/00000000-0000-0000-0000-000000000000",
                      json={"name": "X"})
    assert resp.status_code == 404

    # update ok
    resp = client.put(f"/core-api/admin/rbac/groups/{gid}", json={"description": "d"})
    assert resp.status_code == 200
    assert resp.json["description"] == "d"

    # set_group_roles invalid type -> 400
    resp = client.put(f"/core-api/admin/rbac/groups/{gid}/roles", json={"roleIds": "nope"})
    assert resp.status_code == 400