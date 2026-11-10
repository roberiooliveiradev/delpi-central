"""E2B pelo HTTP (middleware real): redes, conectividade, integrações, dependências e RBAC."""

import pytest

from tests.conftest import (
    ALL_PERMISSIONS,
    integration_payload,
    network_payload,
    server_payload,
    service_payload,
)

MISSING = "00000000-0000-0000-0000-000000000000"


def _create(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _error(response) -> str:
    return response.json()["data"]["error"]["code"]


@pytest.fixture
def srv_api(client):
    return _create(client, "/servers", server_payload(name="SRV-API", hostname="srv-api"))


@pytest.fixture
def network(client):
    return _create(client, "/networks", network_payload())


@pytest.fixture
def services(client):
    portal = _create(client, "/services", service_payload(name="Portal"))
    erp = _create(client, "/services", service_payload(name="Protheus", service_type="erp"))
    return portal, erp


# ------------------------------------------------------------------ redes


def test_network_crud_with_code_and_history(client, network):
    assert network["code"] == "NET-0001"
    assert network["cidr"] == "192.168.1.0/24" and network["server_count"] == 0
    updated = client.put(
        f"/networks/{network['id']}",
        json={**network_payload(vlan_id=20), "revision": network["revision"]},
    )
    assert updated.status_code == 200 and updated.json()["data"]["vlan_id"] == 20
    archived = client.post(f"/networks/{network['id']}/archive", json={"revision": 2})
    assert archived.status_code == 200
    assert client.get("/networks").json()["data"]["total"] == 0
    restored = client.post(f"/networks/{network['id']}/restore", json={"revision": 3})
    assert restored.status_code == 200
    events = [e["event_type"] for e in client.get(f"/networks/{network['id']}/history").json()["data"]]
    assert events == ["network_restored", "network_archived", "network_updated", "network_created"]


def test_network_cidr_validated_by_backend(client):
    response = client.post("/networks", json=network_payload(cidr="192.168.1.7/24"))
    assert response.status_code == 422
    assert "cidr" in response.json()["data"]["error"]["details"]["fields"]


def test_corporate_cidr_is_unique_per_unit_but_container_ranges_repeat(client, network):
    duplicate = client.post("/networks", json=network_payload(name="Outra LAN"))
    assert duplicate.status_code == 409 and _error(duplicate) == "network_cidr_conflict"
    other_unit = client.post("/networks", json=network_payload(name="LAN", unit_code="02"))
    assert other_unit.status_code == 201
    for name in ("bridge srv-api", "bridge srv-app"):
        assert (
            client.post(
                "/networks",
                json=network_payload(
                    name=name, cidr="172.17.0.0/16", gateway=None, network_scope="container_runtime"
                ),
            ).status_code
            == 201
        )


def test_network_filters_and_search(client, network):
    _create(
        client,
        "/networks",
        network_payload(
            name="Docker bridge", cidr="172.17.0.0/16", gateway=None, network_scope="container_runtime"
        ),
    )
    corporate = client.get("/networks", params={"network_scope": "corporate"}).json()["data"]
    assert [n["name"] for n in corporate["items"]] == ["LAN Servidores"]
    assert client.get("/networks", params={"q": "172.17"}).json()["data"]["total"] == 1
    assert client.get("/networks", params={"network_scope": "wifi"}).status_code == 422


# ----------------------------------------------------------- conectividade


def test_server_network_link_lifecycle_preserves_resources(client, srv_api, network):
    link = _create(
        client,
        "/server-network-links",
        {"server_id": srv_api["id"], "network_id": network["id"], "ip_address": "192.168.1.237"},
    )
    assert link["network"]["code"] == "NET-0001" and link["server"]["code"] == srv_api["code"]
    by_server = client.get(f"/servers/{srv_api['id']}/network-links").json()["data"]
    by_network = client.get(f"/networks/{network['id']}/server-links").json()["data"]
    assert [l["id"] for l in by_server] == [l["id"] for l in by_network] == [link["id"]]
    assert client.get(f"/networks/{network['id']}").json()["data"]["server_count"] == 1

    duplicate = client.post(
        "/server-network-links", json={"server_id": srv_api["id"], "network_id": network["id"]}
    )
    assert duplicate.status_code == 409 and _error(duplicate) == "server_network_link_exists"

    removed = client.delete(f"/server-network-links/{link['id']}")
    assert removed.status_code == 200
    assert client.get(f"/servers/{srv_api['id']}").status_code == 200
    assert client.get(f"/networks/{network['id']}").status_code == 200
    assert client.get(f"/servers/{srv_api['id']}/network-links").json()["data"] == []
    server_events = {
        e["event_type"] for e in client.get(f"/servers/{srv_api['id']}/history").json()["data"]
    }
    assert {"server_network_link_created", "server_network_link_removed"} <= server_events


def test_link_ip_must_be_inside_network(client, srv_api, network):
    response = client.post(
        "/server-network-links",
        json={"server_id": srv_api["id"], "network_id": network["id"], "ip_address": "10.0.0.5"},
    )
    assert response.status_code == 422
    assert "ip_address" in response.json()["data"]["error"]["details"]["fields"]


def test_link_rejects_missing_and_archived_references(client, srv_api, network):
    missing = client.post(
        "/server-network-links", json={"server_id": srv_api["id"], "network_id": MISSING}
    )
    assert missing.status_code == 422 and _error(missing) == "reference_not_found"
    client.post(f"/networks/{network['id']}/archive", json={"revision": 1})
    archived = client.post(
        "/server-network-links", json={"server_id": srv_api["id"], "network_id": network["id"]}
    )
    assert archived.status_code == 409 and _error(archived) == "network_archived"


def test_cidr_change_cannot_orphan_linked_ips(client, srv_api, network):
    _create(
        client,
        "/server-network-links",
        {"server_id": srv_api["id"], "network_id": network["id"], "ip_address": "192.168.1.200"},
    )
    shrink = client.put(
        f"/networks/{network['id']}",
        json={**network_payload(cidr="192.168.1.0/25", gateway="192.168.1.1"), "revision": 1},
    )
    assert shrink.status_code == 409 and _error(shrink) == "network_links_outside_cidr"
    widen = client.put(
        f"/networks/{network['id']}",
        json={**network_payload(cidr="192.168.0.0/16", gateway="192.168.1.1"), "revision": 1},
    )
    assert widen.status_code == 200


# ------------------------------------------------------------- integrações


def test_integration_between_services_and_with_external(client, services):
    portal, erp = services
    internal = _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    assert internal["code"] == "INT-0001"
    assert internal["source_service"]["name"] == "Portal"
    assert internal["target_service"]["name"] == "Protheus"
    external = _create(
        client,
        "/integrations",
        integration_payload(
            name="ERP → SEFAZ",
            source_service_id=erp["id"],
            target_external_name="SEFAZ",
            protocol="soap",
        ),
    )
    assert external["target_service"] is None and external["target_external_name"] == "SEFAZ"
    assert client.get("/services").json()["data"]["total"] == 2

    erp_integrations = client.get(f"/services/{erp['id']}/integrations").json()["data"]
    assert {i["code"] for i in erp_integrations} == {"INT-0001", "INT-0002"}
    portal_only = client.get("/integrations", params={"service_id": portal["id"]}).json()["data"]
    assert [i["code"] for i in portal_only["items"]] == ["INT-0001"]
    assert client.get("/integrations", params={"q": "sefaz"}).json()["data"]["total"] == 1


def test_integration_rejects_nonexistent_duplicate_and_self(client, services):
    portal, erp = services
    missing = client.post(
        "/integrations",
        json=integration_payload(source_service_id=portal["id"], target_service_id=MISSING),
    )
    assert missing.status_code == 422 and _error(missing) == "reference_not_found"
    assert "target_service_id" in missing.json()["data"]["error"]["details"]["fields"]

    _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    duplicate = client.post(
        "/integrations",
        json=integration_payload(
            name="Outro nome", source_service_id=portal["id"], target_service_id=erp["id"]
        ),
    )
    assert duplicate.status_code == 409 and _error(duplicate) == "integration_exists"
    other_protocol = client.post(
        "/integrations",
        json=integration_payload(
            name="Arquivos", source_service_id=portal["id"], target_service_id=erp["id"], protocol="smb"
        ),
    )
    assert other_protocol.status_code == 201

    self_relation = client.post(
        "/integrations",
        json=integration_payload(source_service_id=portal["id"], target_service_id=portal["id"]),
    )
    assert self_relation.status_code == 422


def test_external_names_are_case_insensitive_for_duplicates(client, services):
    portal, _ = services
    _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_external_name="Banco Itaú"),
    )
    duplicate = client.post(
        "/integrations",
        json=integration_payload(
            name="Itaú 2", source_service_id=portal["id"], target_external_name="banco itaú"
        ),
    )
    assert duplicate.status_code == 409


def test_archiving_integration_keeps_services_and_blocks_edits(client, services):
    portal, erp = services
    integration = _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    archived = client.post(f"/integrations/{integration['id']}/archive", json={"revision": 1})
    assert archived.status_code == 200
    assert client.get(f"/services/{portal['id']}").json()["data"]["archived"] is False
    edit = client.put(
        f"/integrations/{integration['id']}",
        json={
            **integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
            "revision": 2,
        },
    )
    assert edit.status_code == 409 and _error(edit) == "integration_archived"
    portal_history = {
        e["event_type"] for e in client.get(f"/services/{portal['id']}/history").json()["data"]
    }
    assert {"integration_created", "integration_archived"} <= portal_history


def test_archived_service_cannot_receive_new_integration(client, services):
    portal, erp = services
    client.post(f"/services/{erp['id']}/archive", json={"revision": 1})
    response = client.post(
        "/integrations",
        json=integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    assert response.status_code == 409 and _error(response) == "service_archived"


# ------------------------------------------------------- página do servidor


def test_server_page_shows_services_databases_networks_and_integrations(
    client, srv_api, network, services
):
    portal, erp = services
    client.post(
        "/service-hostings",
        json={"service_id": portal["id"], "server_id": srv_api["id"], "runtime": "container"},
    )
    _create(
        client,
        "/database-instances",
        {
            "name": "portal_db",
            "dbms": "postgresql",
            "server_id": srv_api["id"],
            "environment": "production",
            "criticality": "high",
            "responsible": "Equipe Infra",
            "administrative_status": "in_operation",
        },
    )
    _create(
        client,
        "/server-network-links",
        {"server_id": srv_api["id"], "network_id": network["id"], "ip_address": "192.168.1.237"},
    )
    _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    sid = srv_api["id"]
    assert [h["service"]["name"] for h in client.get(f"/servers/{sid}/service-hostings").json()["data"]] == ["Portal"]
    assert client.get("/database-instances", params={"server_id": sid}).json()["data"]["total"] == 1
    assert [l["network"]["cidr"] for l in client.get(f"/servers/{sid}/network-links").json()["data"]] == [
        "192.168.1.0/24"
    ]
    assert [i["name"] for i in client.get(f"/servers/{sid}/integrations").json()["data"]] == [
        "Portal → ERP"
    ]


def test_server_without_hosted_services_has_no_integrations(client, srv_api, services):
    portal, erp = services
    _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    assert client.get(f"/servers/{srv_api['id']}/integrations").json()["data"] == []


# ------------------------------------------------------------ dependências


def test_dependency_lifecycle_and_rules(client, services):
    portal, erp = services
    dependency = _create(
        client,
        "/service-dependencies",
        {"dependent_service_id": portal["id"], "required_service_id": erp["id"]},
    )
    listed_portal = client.get(f"/services/{portal['id']}/dependencies").json()["data"]
    listed_erp = client.get(f"/services/{erp['id']}/dependencies").json()["data"]
    assert [d["id"] for d in listed_portal] == [d["id"] for d in listed_erp] == [dependency["id"]]
    assert dependency["required_service"]["name"] == "Protheus"

    duplicate = client.post(
        "/service-dependencies",
        json={"dependent_service_id": portal["id"], "required_service_id": erp["id"]},
    )
    assert duplicate.status_code == 409 and _error(duplicate) == "service_dependency_exists"
    self_dep = client.post(
        "/service-dependencies",
        json={"dependent_service_id": portal["id"], "required_service_id": portal["id"]},
    )
    assert self_dep.status_code == 422
    missing = client.post(
        "/service-dependencies",
        json={"dependent_service_id": portal["id"], "required_service_id": MISSING},
    )
    assert missing.status_code == 422 and _error(missing) == "reference_not_found"

    assert client.delete(f"/service-dependencies/{dependency['id']}").status_code == 200
    assert client.get(f"/services/{erp['id']}").status_code == 200
    assert client.get(f"/services/{portal['id']}/dependencies").json()["data"] == []


def test_relations_are_not_presumed_from_other_links(client, services):
    portal, erp = services
    _create(
        client,
        "/integrations",
        integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
    )
    assert client.get(f"/services/{portal['id']}/dependencies").json()["data"] == []


# --------------------------------------------------------------------- RBAC

NETWORK_READS = ["/networks", "/servers/{sid}/network-links"]
INTEGRATION_READS = ["/integrations", "/services/{svc}/integrations", "/servers/{sid}/integrations"]


def _paths(paths, srv, svc):
    return [p.format(sid=srv["id"], svc=svc["id"]) for p in paths]


def test_new_data_is_hidden_without_specific_view_permissions(client, principal, srv_api, services):
    portal, _ = services
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.services.view",
        "it-portal.databases.view",
    ]
    for path in _paths(NETWORK_READS + INTEGRATION_READS, srv_api, portal):
        assert client.get(path).status_code == 403, path
    assert client.get(f"/services/{portal['id']}/dependencies").status_code == 200
    caps = client.get("/me/capabilities").json()["data"]
    assert not any(caps[key] for key in caps if "network" in key or "integration" in key)


def test_view_permissions_read_but_cannot_write(client, principal, srv_api, network, services):
    portal, erp = services
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.services.view",
        "it-portal.networks.view",
        "it-portal.integrations.view",
    ]
    for path in _paths(NETWORK_READS + INTEGRATION_READS, srv_api, portal):
        assert client.get(path).status_code == 200, path
    assert client.post("/networks", json=network_payload(name="Nova")).status_code == 403
    assert (
        client.post(
            "/server-network-links", json={"server_id": srv_api["id"], "network_id": network["id"]}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/integrations",
            json=integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/service-dependencies",
            json={"dependent_service_id": portal["id"], "required_service_id": erp["id"]},
        ).status_code
        == 403
    )


def test_manage_without_view_is_forbidden(client, principal):
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.services.view",
        "it-portal.networks.manage",
        "it-portal.integrations.manage",
    ]
    assert client.post("/networks", json=network_payload()).status_code == 403
    caps = client.get("/me/capabilities").json()["data"]
    assert caps["can_manage_networks"] is False and caps["can_manage_integrations"] is False


def test_integrations_view_requires_services_view(client, principal):
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.integrations.view",
    ]
    assert client.get("/integrations").status_code == 403
    assert client.get("/me/capabilities").json()["data"]["can_view_integrations"] is False


def test_full_permissions_capabilities(client, principal):
    principal.permissions = list(ALL_PERMISSIONS)
    caps = client.get("/me/capabilities").json()["data"]
    assert caps["can_view_networks"] and caps["can_manage_networks"]
    assert caps["can_view_integrations"] and caps["can_manage_integrations"]


def test_new_writes_revalidate_fresh_rbac(client, principal, services):
    portal, erp = services
    principal.fresh_permissions = [
        p for p in ALL_PERMISSIONS if p not in ("it-portal.networks.manage", "it-portal.integrations.manage")
    ]
    assert client.post("/networks", json=network_payload()).status_code == 403
    assert (
        client.post(
            "/integrations",
            json=integration_payload(source_service_id=portal["id"], target_service_id=erp["id"]),
        ).status_code
        == 403
    )


def test_anonymous_cannot_read_new_routes(repository):
    from fastapi.testclient import TestClient

    from it_portal_app.main import app

    with TestClient(app) as anonymous:
        for path in ("/networks", "/integrations", f"/services/{MISSING}/dependencies"):
            assert anonymous.get(path).status_code == 401
