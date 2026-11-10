"""Contrato HTTP, RBAC e regras de vínculo do inventário E2A (repositório em memória)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from it_portal_app.interface.http.schemas import ServerOut
from it_portal_app.main import app

from tests.conftest import database_payload, server_payload, service_payload

INVENTORY_READ = [
    "it-portal.access",
    "it-portal.servers.view",
    "it-portal.services.view",
    "it-portal.databases.view",
]
RANDOM_ID = "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"

SERVICE_READ_ROUTES = [
    ("get", "/services"),
    ("get", f"/services/{RANDOM_ID}"),
    ("get", f"/services/{RANDOM_ID}/history"),
    ("get", f"/services/{RANDOM_ID}/hostings"),
    ("get", f"/servers/{RANDOM_ID}/service-hostings"),
]
DATABASE_READ_ROUTES = [
    ("get", "/database-instances"),
    ("get", f"/database-instances/{RANDOM_ID}"),
    ("get", f"/database-instances/{RANDOM_ID}/history"),
]


def _server(client, **overrides) -> dict:
    response = client.post("/servers", json=server_payload(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _service(client, **overrides) -> dict:
    response = client.post("/services", json=service_payload(**overrides))
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _database(client, server_id: str, **overrides) -> dict:
    response = client.post("/database-instances", json=database_payload(server_id, **overrides))
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _error_code(response) -> str:
    return response.json()["data"]["error"]["code"]


# ------------------------------------------------------------------- AuthN/Z


@pytest.mark.parametrize("method, path", SERVICE_READ_ROUTES + DATABASE_READ_ROUTES)
def test_inventory_routes_require_token(method, path, repository):
    with TestClient(app) as anonymous:
        assert getattr(anonymous, method)(path).status_code == 401


@pytest.mark.parametrize("method, path", SERVICE_READ_ROUTES)
def test_servers_view_alone_does_not_grant_services(method, path, client, principal):
    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    assert getattr(client, method)(path).status_code == 403


@pytest.mark.parametrize("method, path", DATABASE_READ_ROUTES)
def test_servers_view_alone_does_not_grant_databases(method, path, client, principal):
    principal.permissions = ["it-portal.access", "it-portal.servers.view", "it-portal.services.view"]
    assert getattr(client, method)(path).status_code == 403


def test_resource_view_without_servers_view_is_forbidden(client, principal):
    principal.permissions = ["it-portal.access", "it-portal.services.view", "it-portal.databases.view"]
    assert client.get("/services").status_code == 403
    assert client.get("/database-instances").status_code == 403


def test_viewers_read_but_cannot_write(client, principal, inventory):
    server = _server(client)
    service = _service(client)
    database = _database(client, server["id"])
    principal.permissions = INVENTORY_READ
    assert client.get("/services").json()["data"]["total"] == 1
    assert client.get(f"/database-instances/{database['id']}").status_code == 200
    assert client.post("/services", json=service_payload(name="Outro")).status_code == 403
    assert (
        client.put(f"/services/{service['id']}", json={**service_payload(), "revision": 1}).status_code
        == 403
    )
    assert client.post(f"/services/{service['id']}/archive", json={"revision": 1}).status_code == 403
    assert (
        client.post(
            "/service-hostings",
            json={"service_id": service["id"], "server_id": server["id"], "runtime": "container"},
        ).status_code
        == 403
    )
    assert client.post("/database-instances", json=database_payload(server["id"], name="x")).status_code == 403
    assert (
        client.post(
            "/database-consumers",
            json={"database_instance_id": database["id"], "service_id": service["id"]},
        ).status_code
        == 403
    )
    assert len(inventory.services) == 1 and not inventory.hostings and not inventory.consumers


def test_database_manager_needs_services_view_to_link_consumers(client, principal):
    server = _server(client)
    service = _service(client)
    database = _database(client, server["id"])
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.databases.view",
        "it-portal.databases.manage",
    ]
    body = {"database_instance_id": database["id"], "service_id": service["id"]}
    assert client.post("/database-consumers", json=body).status_code == 403
    assert client.get(f"/database-instances/{database['id']}/consumers").status_code == 403
    principal.permissions.append("it-portal.services.view")
    assert client.post("/database-consumers", json=body).status_code == 201


def test_capabilities_expose_inventory_flags_without_widening_access(client, principal):
    principal.permissions = ["it-portal.access", "it-portal.servers.view", "it-portal.services.manage"]
    data = client.get("/me/capabilities").json()["data"]
    assert data["can_view_services"] is False
    assert data["can_manage_services"] is False
    assert data["can_view_databases"] is False
    principal.permissions = [
        "it-portal.access",
        "it-portal.services.view",
        "it-portal.services.manage",
        "it-portal.databases.view",
    ]
    data = client.get("/me/capabilities").json()["data"]
    assert data["can_view_services"] is False and data["can_view_databases"] is False
    principal.permissions = [*INVENTORY_READ, "it-portal.services.manage"]
    data = client.get("/me/capabilities").json()["data"]
    assert data["can_view_services"] and data["can_manage_services"]
    assert data["can_view_databases"] and not data["can_manage_databases"]


# --------------------------------------------------------------- services AC-01


def test_service_crud_archive_and_restore(client, repository):
    created = _service(client)
    assert created["code"] == "SVC-0001"
    assert created["hosting_count"] == 0 and created["database_count"] == 0

    updated = client.put(
        f"/services/{created['id']}", json={**service_payload(criticality="critical"), "revision": 1}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["revision"] == 2

    stale = client.put(f"/services/{created['id']}", json={**service_payload(port=9000), "revision": 1})
    assert stale.status_code == 409 and _error_code(stale) == "revision_conflict"

    archived = client.post(f"/services/{created['id']}/archive", json={"revision": 2}).json()["data"]
    assert archived["archived"] is True
    assert client.get("/services").json()["data"]["total"] == 0
    assert client.get("/services", params={"archived": "archived"}).json()["data"]["total"] == 1

    read_only = client.put(f"/services/{created['id']}", json={**service_payload(), "revision": 3})
    assert read_only.status_code == 409 and _error_code(read_only) == "service_archived"

    restored = client.post(f"/services/{created['id']}/restore", json={"revision": 3})
    assert restored.status_code == 200 and restored.json()["data"]["archived"] is False

    history = client.get(f"/services/{created['id']}/history").json()["data"]
    assert [event["event_type"] for event in history] == [
        "service_restored",
        "service_archived",
        "service_updated",
        "service_created",
    ]
    assert history[2]["changes"] == {"criticality": {"from": "high", "to": "critical"}}
    assert all(event["entity_type"] == "service" for event in history)
    assert all(event.get("server_id") is None for event in repository.audit)


def test_service_identity_is_unique_per_unit_and_environment(client):
    _service(client, name="Portal Interno")
    duplicate = client.post("/services", json=service_payload(name="PORTAL INTERNO"))
    assert duplicate.status_code == 409 and _error_code(duplicate) == "service_identity_conflict"
    assert client.post("/services", json=service_payload(environment="staging")).status_code == 201
    assert client.post("/services", json=service_payload(unit_code="02")).status_code == 201


def test_service_validation_errors_are_reported_per_field(client):
    response = client.post("/services", json=service_payload(responsible="", port=70000))
    assert response.status_code == 422
    assert set(response.json()["data"]["error"]["details"]["fields"]) == {"responsible", "port"}


def test_service_listing_filters_and_validates_query(client):
    _service(client, name="Keycloak", service_kind="platform_service", service_type="identity_access")
    _service(client, name="Portal Interno")
    platform = client.get("/services", params={"service_kind": "platform_service"}).json()["data"]
    assert [item["name"] for item in platform["items"]] == ["Keycloak"]
    by_tech = client.get("/services", params={"q": "fastapi"}).json()["data"]
    assert by_tech["total"] == 2
    invalid = client.get("/services", params={"service_kind": "container"})
    assert invalid.status_code == 422 and _error_code(invalid) == "invalid_query"


def test_missing_service_is_404(client):
    response = client.get(f"/services/{uuid.uuid4()}")
    assert response.status_code == 404 and _error_code(response) == "service_not_found"


# ------------------------------------------------------- hostings AC-02 / AC-07


def test_service_links_to_multiple_servers_and_unlink_preserves_resources(client, repository, inventory):
    primary = _server(client, hostname="srv-app-01")
    secondary = _server(client, hostname="srv-app-02")
    service = _service(client)

    links = []
    for server, runtime in ((primary, "container"), (secondary, "native_process")):
        response = client.post(
            "/service-hostings",
            json={
                "service_id": service["id"],
                "server_id": server["id"],
                "runtime": runtime,
                "instance_name": "portal-api",
            },
        )
        assert response.status_code == 201
        links.append(response.json()["data"])
    assert links[0]["server"]["code"] == primary["code"]
    assert links[0]["service"]["code"] == service["code"]

    assert client.get(f"/services/{service['id']}").json()["data"]["hosting_count"] == 2
    hosted = client.get(f"/servers/{primary['id']}/service-hostings").json()["data"]
    assert [h["service_id"] for h in hosted] == [service["id"]]

    removed = client.delete(f"/service-hostings/{links[0]['id']}")
    assert removed.status_code == 200 and removed.json()["data"] == {"id": links[0]["id"]}
    assert client.get(f"/services/{service['id']}").status_code == 200
    assert client.get(f"/servers/{primary['id']}").status_code == 200
    assert client.get(f"/servers/{primary['id']}/service-hostings").json()["data"] == []
    assert len(client.get(f"/services/{service['id']}/hostings").json()["data"]) == 1

    again = client.delete(f"/service-hostings/{links[0]['id']}")
    assert again.status_code == 404 and _error_code(again) == "service_hosting_not_found"

    server_history = client.get(f"/servers/{primary['id']}/history").json()["data"]
    assert [e["event_type"] for e in server_history][:2] == [
        "service_hosting_removed",
        "service_hosting_created",
    ]
    assert server_history[0]["changes"]["service"]["code"] == service["code"]
    service_history = client.get(f"/services/{service['id']}/history").json()["data"]
    assert {e["event_type"] for e in service_history} >= {
        "service_hosting_created",
        "service_hosting_removed",
    }


def test_hosting_rejects_duplicates_missing_and_archived_references(client):
    server = _server(client)
    service = _service(client)
    body = {"service_id": service["id"], "server_id": server["id"], "runtime": "container"}
    assert client.post("/service-hostings", json=body).status_code == 201

    duplicate = client.post("/service-hostings", json=body)
    assert duplicate.status_code == 409 and _error_code(duplicate) == "service_hosting_exists"

    missing = client.post("/service-hostings", json={**body, "server_id": str(uuid.uuid4())})
    assert missing.status_code == 422 and _error_code(missing) == "reference_not_found"
    assert "server_id" in missing.json()["data"]["error"]["details"]["fields"]

    other = _server(client, hostname="srv-archived-01")
    client.post(f"/servers/{other['id']}/archive", json={"revision": 1})
    archived = client.post("/service-hostings", json={**body, "server_id": other["id"]})
    assert archived.status_code == 409 and _error_code(archived) == "server_archived"

    invalid = client.post("/service-hostings", json={**body, "runtime": "kubernetes"})
    assert invalid.status_code == 422


def test_archived_service_cannot_receive_new_links(client):
    server = _server(client)
    service = _service(client)
    client.post(f"/services/{service['id']}/archive", json={"revision": 1})
    response = client.post(
        "/service-hostings",
        json={"service_id": service["id"], "server_id": server["id"], "runtime": "container"},
    )
    assert response.status_code == 409 and _error_code(response) == "service_archived"


# ------------------------------------------------------------ databases AC-03


def test_database_crud_links_to_host_and_consumers(client):
    host = _server(client)
    database = _database(client, host["id"])
    assert database["code"] == "DB-0001"
    assert database["server"]["id"] == host["id"]

    same_name_other_host = _server(client, hostname="srv-db-02")
    duplicate = client.post("/database-instances", json=database_payload(host["id"], name="ERP_PROD"))
    assert duplicate.status_code == 409 and _error_code(duplicate) == "database_identity_conflict"
    assert (
        client.post("/database-instances", json=database_payload(same_name_other_host["id"])).status_code
        == 201
    )

    service = _service(client)
    other_service = _service(client, name="Integrador")
    for consumer in (service, other_service):
        response = client.post(
            "/database-consumers",
            json={"database_instance_id": database["id"], "service_id": consumer["id"], "notes": "Leitura"},
        )
        assert response.status_code == 201
    consumers = client.get(f"/database-instances/{database['id']}/consumers").json()["data"]
    assert {c["service"]["name"] for c in consumers} == {"Portal Interno", "Integrador"}
    assert client.get(f"/database-instances/{database['id']}").json()["data"]["consumer_count"] == 2
    service_dbs = client.get(f"/services/{service['id']}/database-instances").json()["data"]
    assert [link["database"]["code"] for link in service_dbs] == ["DB-0001"]

    duplicate_link = client.post(
        "/database-consumers",
        json={"database_instance_id": database["id"], "service_id": service["id"]},
    )
    assert duplicate_link.status_code == 409 and _error_code(duplicate_link) == "database_consumer_exists"

    removed = client.delete(f"/database-consumers/{consumers[0]['id']}")
    assert removed.status_code == 200
    assert client.get(f"/database-instances/{database['id']}").json()["data"]["consumer_count"] == 1
    assert client.get(f"/services/{consumers[0]['service_id']}").status_code == 200

    hosted = client.get("/database-instances", params={"server_id": host["id"]}).json()["data"]
    assert [item["id"] for item in hosted["items"]] == [database["id"]]


def test_database_requires_active_existing_host(client):
    missing = client.post("/database-instances", json=database_payload(str(uuid.uuid4())))
    assert missing.status_code == 422 and _error_code(missing) == "reference_not_found"
    host = _server(client)
    client.post(f"/servers/{host['id']}/archive", json={"revision": 1})
    archived = client.post("/database-instances", json=database_payload(host["id"]))
    assert archived.status_code == 409 and _error_code(archived) == "server_archived"


def test_database_rejects_credentials(client):
    host = _server(client)
    response = client.post(
        "/database-instances",
        json=database_payload(host["id"], technical_notes="postgresql://app:Sup3rS3cret@db01/erp"),
    )
    assert response.status_code == 422 and _error_code(response) == "secret_not_allowed"


def test_moving_database_appears_in_both_server_histories(client):
    first = _server(client, hostname="srv-db-01")
    second = _server(client, hostname="srv-db-02")
    database = _database(client, first["id"])
    moved = client.put(
        f"/database-instances/{database['id']}",
        json={**database_payload(second["id"]), "revision": 1},
    )
    assert moved.status_code == 200 and moved.json()["data"]["server"]["id"] == second["id"]
    for server in (first, second):
        events = client.get(f"/servers/{server['id']}/history").json()["data"]
        assert "database_instance_updated" in {e["event_type"] for e in events}
    db_history = client.get(f"/database-instances/{database['id']}/history").json()["data"]
    assert db_history[0]["changes"]["server_id"] == {"from": first["id"], "to": second["id"]}


def test_archived_database_is_read_only_and_restorable(client):
    host = _server(client)
    database = _database(client, host["id"])
    service = _service(client)
    client.post(f"/database-instances/{database['id']}/archive", json={"revision": 1})
    edit = client.put(
        f"/database-instances/{database['id']}", json={**database_payload(host["id"]), "revision": 2}
    )
    assert edit.status_code == 409 and _error_code(edit) == "database_instance_archived"
    link = client.post(
        "/database-consumers",
        json={"database_instance_id": database["id"], "service_id": service["id"]},
    )
    assert link.status_code == 409 and _error_code(link) == "database_instance_archived"
    restored = client.post(f"/database-instances/{database['id']}/restore", json={"revision": 2})
    assert restored.status_code == 200


def test_etapa1_server_contract_is_unchanged(client):
    etapa1_fields = {
        "id", "code", "name", "hostname", "ip_address", "unit_code", "location", "environment",
        "server_type", "purpose", "operating_system", "criticality", "administrative_status",
        "responsible", "description", "revision", "archived", "archived_at", "archived_by_name",
        "open_action_count", "created_at", "created_by_name", "updated_at", "updated_by_name",
    }
    assert set(ServerOut.model_fields) == etapa1_fields
    assert etapa1_fields <= set(_server(client))
