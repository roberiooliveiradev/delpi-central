"""R-SEC-01 — escritas revalidam a permissão efetiva no Core (sem cache/stale)
e `manage` não dispensa a permissão de leitura do recurso."""

import pytest

from tests.conftest import ALL_PERMISSIONS, database_payload, server_payload, service_payload

SERVER_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"


def _create_server(client, **overrides):
    response = client.post("/servers", json=server_payload(**overrides))
    assert response.status_code == 201
    return response.json()["data"]


def _write_cases(client):
    server = _create_server(client)
    to_archive = _create_server(client, hostname="srv-arquivar")
    service = client.post("/services", json=service_payload()).json()["data"]
    return [
        ("post", "/servers", server_payload(hostname="srv-novo")),
        ("put", f"/servers/{server['id']}", {**server_payload(), "revision": server["revision"]}),
        ("post", f"/servers/{to_archive['id']}/archive", {"revision": to_archive["revision"]}),
        ("post", f"/servers/{server['id']}/notes", {"body": "Reiniciado."}),
        ("post", f"/servers/{server['id']}/action-plans", {"title": "Patch", "priority": "low"}),
        ("post", "/services", service_payload(name="Outro serviço")),
        ("put", f"/services/{service['id']}", {**service_payload(), "revision": service["revision"]}),
        ("post", "/database-instances", database_payload(server["id"], name="outro_db")),
        (
            "post",
            "/service-hostings",
            {"service_id": service["id"], "server_id": server["id"], "runtime": "container"},
        ),
    ]


def _send(client, method, path, body):
    return getattr(client, method)(path, json=body)


def test_server_manage_without_view_is_forbidden(client, principal, repository):
    principal.permissions = ["it-portal.access", "it-portal.servers.manage"]
    assert client.post("/servers", json=server_payload()).status_code == 403
    assert len(repository.servers) == 0


def test_server_manage_with_view_writes(client, principal, repository):
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.servers.manage",
    ]
    assert client.post("/servers", json=server_payload()).status_code == 201


def test_every_write_revalidates_against_core(client, principal):
    cases = _write_cases(client)
    for method, path, body in cases:
        before = principal.fresh_lookups
        response = _send(client, method, path, body)
        assert response.status_code in (200, 201), (method, path, response.json())
        assert principal.fresh_lookups == before + 1, (method, path)


def test_reads_do_not_require_fresh_lookup(client, principal):
    _create_server(client)
    before = principal.fresh_lookups
    assert client.get("/servers").status_code == 200
    assert client.get("/services").status_code == 200
    assert client.get("/me/capabilities").status_code == 200
    assert principal.fresh_lookups == before


def test_permission_revoked_after_cache_blocks_every_write(client, principal, repository, inventory):
    cases = _write_cases(client)
    servers_before = len(repository.servers)
    principal.fresh_permissions = ["it-portal.access", "it-portal.servers.view"]
    for method, path, body in cases:
        response = _send(client, method, path, body)
        assert response.status_code == 403, (method, path)
    assert len(repository.servers) == servers_before


@pytest.mark.parametrize("revoked", ["it-portal.access", "it-portal.services.manage"])
def test_revocation_of_any_required_permission_blocks(client, principal, revoked):
    principal.fresh_permissions = [p for p in ALL_PERMISSIONS if p != revoked]
    assert client.post("/services", json=service_payload()).status_code == 403


def test_core_unavailable_on_fresh_lookup_fails_closed(client, principal, repository):
    _create_server(client)
    principal.fresh_unavailable = True
    response = client.post("/servers", json=server_payload(hostname="srv-stale"))
    assert response.status_code == 503
    assert len(repository.servers) == 1
    assert client.get("/servers").status_code == 200


def test_fresh_principal_is_the_audited_author(client, principal, repository):
    server = _create_server(client)
    response = client.post(f"/servers/{server['id']}/notes", json={"body": "Ok."})
    assert response.json()["data"]["author_name"] == "Ana TI"


def test_unknown_server_write_still_requires_permissions(client, principal):
    principal.permissions = ["it-portal.access"]
    response = client.put(f"/servers/{SERVER_ID}", json={**server_payload(), "revision": 1})
    assert response.status_code == 403
