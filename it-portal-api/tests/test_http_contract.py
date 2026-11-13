"""Contrato HTTP: OpenAPI, envelopes, validação, paginação e erros."""

from it_portal_app.main import app

from tests.conftest import server_payload

EXPECTED_OPERATIONS = {
    ("get", "/health"): "get_it_portal_health",
    ("get", "/me/capabilities"): "get_it_portal_capabilities",
    ("get", "/dashboard"): "get_it_portal_dashboard",
    ("get", "/workstations"): "list_it_workstations",
    ("post", "/workstations"): "create_it_workstation",
    ("get", "/workstations/{workstation_id}"): "get_it_workstation",
    ("put", "/workstations/{workstation_id}"): "update_it_workstation",
    ("post", "/workstations/{workstation_id}/archive"): "archive_it_workstation",
    ("post", "/workstations/{workstation_id}/restore"): "restore_it_workstation",
    ("get", "/workstations/{workstation_id}/history"): "list_it_workstation_history",
    ("get", "/workstations/{workstation_id}/snapshot"): "get_it_workstation_latest_snapshot",
    ("post", "/collector/v1/workstations/{workstation_id}/snapshots"): "ingest_it_workstation_snapshot",
    ("get", "/servers"): "list_it_servers",
    ("post", "/servers"): "create_it_server",
    ("get", "/servers/{server_id}"): "get_it_server",
    ("put", "/servers/{server_id}"): "update_it_server",
    ("post", "/servers/{server_id}/archive"): "archive_it_server",
    ("post", "/servers/{server_id}/restore"): "restore_it_server",
    ("get", "/servers/{server_id}/notes"): "list_it_server_notes",
    ("post", "/servers/{server_id}/notes"): "create_it_server_note",
    ("get", "/servers/{server_id}/history"): "list_it_server_history",
    ("get", "/action-plans"): "list_it_action_plans",
    ("post", "/servers/{server_id}/action-plans"): "create_it_action_plan",
    ("get", "/action-plans/{action_plan_id}"): "get_it_action_plan",
    ("put", "/action-plans/{action_plan_id}"): "update_it_action_plan",
    ("post", "/action-plans/{action_plan_id}/status"): "change_it_action_plan_status",
    # E2A — serviços, instâncias de banco e vínculos
    ("get", "/services"): "list_it_services",
    ("post", "/services"): "create_it_service",
    ("get", "/services/{service_id}"): "get_it_service",
    ("put", "/services/{service_id}"): "update_it_service",
    ("post", "/services/{service_id}/archive"): "archive_it_service",
    ("post", "/services/{service_id}/restore"): "restore_it_service",
    ("get", "/services/{service_id}/history"): "list_it_service_history",
    ("get", "/services/{service_id}/hostings"): "list_it_service_hostings",
    ("get", "/services/{service_id}/database-instances"): "list_it_service_database_links",
    ("get", "/servers/{server_id}/service-hostings"): "list_it_server_service_hostings",
    ("post", "/service-hostings"): "create_it_service_hosting",
    ("delete", "/service-hostings/{hosting_id}"): "delete_it_service_hosting",
    ("get", "/database-instances"): "list_it_database_instances",
    ("post", "/database-instances"): "create_it_database_instance",
    ("get", "/database-instances/{database_id}"): "get_it_database_instance",
    ("put", "/database-instances/{database_id}"): "update_it_database_instance",
    ("post", "/database-instances/{database_id}/archive"): "archive_it_database_instance",
    ("post", "/database-instances/{database_id}/restore"): "restore_it_database_instance",
    ("get", "/database-instances/{database_id}/history"): "list_it_database_instance_history",
    ("get", "/database-instances/{database_id}/consumers"): "list_it_database_consumers",
    ("post", "/database-consumers"): "create_it_database_consumer",
    ("delete", "/database-consumers/{consumer_id}"): "delete_it_database_consumer",
    # E2B — redes, conectividade, integrações e dependências operacionais
    ("get", "/networks"): "list_it_networks",
    ("post", "/networks"): "create_it_network",
    ("get", "/networks/{network_id}"): "get_it_network",
    ("put", "/networks/{network_id}"): "update_it_network",
    ("post", "/networks/{network_id}/archive"): "archive_it_network",
    ("post", "/networks/{network_id}/restore"): "restore_it_network",
    ("get", "/networks/{network_id}/history"): "list_it_network_history",
    ("get", "/networks/{network_id}/server-links"): "list_it_network_server_links",
    ("get", "/servers/{server_id}/network-links"): "list_it_server_network_links",
    ("post", "/server-network-links"): "create_it_server_network_link",
    ("delete", "/server-network-links/{link_id}"): "delete_it_server_network_link",
    ("get", "/integrations"): "list_it_integrations",
    ("post", "/integrations"): "create_it_integration",
    ("get", "/integrations/{integration_id}"): "get_it_integration",
    ("put", "/integrations/{integration_id}"): "update_it_integration",
    ("post", "/integrations/{integration_id}/archive"): "archive_it_integration",
    ("post", "/integrations/{integration_id}/restore"): "restore_it_integration",
    ("get", "/integrations/{integration_id}/history"): "list_it_integration_history",
    ("get", "/services/{service_id}/integrations"): "list_it_service_integrations",
    ("get", "/servers/{server_id}/integrations"): "list_it_server_integrations",
    ("get", "/services/{service_id}/dependencies"): "list_it_service_dependencies",
    ("post", "/service-dependencies"): "create_it_service_dependency",
    ("delete", "/service-dependencies/{dependency_id}"): "delete_it_service_dependency",
    # #1576 P1 — inventário completo e dedicado Windows SCM
    ("post", "/collector/v1/servers/{server_id}/host-services/batches"): "ingest_it_windows_host_service_batch",
    ("get", "/servers/{server_id}/host-services"): "list_it_windows_host_services",
    ("put", "/servers/{server_id}/host-services/{service_name}/preferences"): "set_it_windows_host_service_preference",
    ("post", "/servers/{server_id}/host-services/{service_name}/actions"): "request_it_windows_host_service_action",
    ("get", "/servers/{server_id}/host-services/actions/{action_id}"): "get_it_windows_host_service_action",
    ("post", "/collector/v1/servers/{server_id}/host-services/control/next"): "claim_it_windows_host_service_action",
    ("post", "/collector/v1/servers/{server_id}/host-services/control/{action_id}/result"): "report_it_windows_host_service_action",
    # E4.S1 — observações automáticas
    ("post", "/collector/v1/servers/{server_id}/observations"): "ingest_it_server_observation",
}


# Endpoints introduced by independently deployed Windows monitoring and E4.S1
# observations may be present according to the API's feature assembly.
# Keep stable IDs verified whenever exported, without making this unrelated
# legacy agent patch depend on those optional surface combinations.
OPTIONAL_OPERATIONS = {
    ("get", "/dashboard/windows-services-health"): "get_it_windows_services_health",
    ("get", "/servers/{server_id}/observations/latest"): "get_it_server_latest_observation",
    ("get", "/servers/{server_id}/observations"): "list_it_server_observations",
}


def test_openapi_operation_ids_are_explicit_stable_and_unique():
    schema = app.openapi()
    found = {
        (method, path): operation["operationId"]
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
    }
    required_found = {key: value for key, value in found.items() if key not in OPTIONAL_OPERATIONS}
    assert required_found == EXPECTED_OPERATIONS
    for key, operation_id in OPTIONAL_OPERATIONS.items():
        if key in found:
            assert found[key] == operation_id
    assert len(set(found.values())) == len(found)


def test_openapi_declares_distinct_security_for_workstation_collector():
    schema = app.openapi()
    security = schema["components"]["securitySchemes"]
    assert security["bearerAuth"]["scheme"] == "bearer"
    assert security["workstationCollectorS2S"]["name"] == "X-Delpi-Service-Authorization"
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            if path == "/health":
                assert "security" not in operation
            elif path.startswith("/collector/v1/workstations/"):
                assert operation["security"] == [{"workstationCollectorS2S": []}]
            else:
                assert operation["security"] == [{"bearerAuth": []}]


def test_create_returns_envelope_with_operation_id(client):
    response = client.post("/servers", json=server_payload())
    body = response.json()
    assert response.status_code == 201
    assert body["success"] is True
    assert body["meta"] == {"operationId": "create_it_server"}
    assert body["data"]["code"] == "SRV-0001"
    assert body["data"]["hostname"] == "srv-erp-01.delpi.local"


def test_backend_validation_returns_field_errors(client):
    response = client.post(
        "/servers", json=server_payload(hostname="srv erp", ip_address="10.0.0.300")
    )
    body = response.json()
    assert response.status_code == 422
    assert body["data"]["error"]["code"] == "invalid_server"
    assert set(body["data"]["error"]["details"]["fields"]) == {"hostname", "ip_address"}


def test_unknown_fields_are_rejected(client):
    response = client.post("/servers", json={**server_payload(), "uptime": "99.9%"})
    assert response.status_code == 422
    assert response.json()["data"]["error"]["code"] == "invalid_request"


def test_duplicate_identity_is_conflict(client):
    client.post("/servers", json=server_payload())
    response = client.post("/servers", json=server_payload())
    assert response.status_code == 409
    assert response.json()["data"]["error"]["code"] == "server_identity_conflict"


def test_note_with_secret_is_rejected(client):
    server = client.post("/servers", json=server_payload()).json()["data"]
    response = client.post(
        f"/servers/{server['id']}/notes", json={"body": "usuario admin senha: Delpi@2026!"}
    )
    assert response.status_code == 422
    assert response.json()["data"]["error"]["code"] == "secret_not_allowed"


def test_list_supports_search_filters_sort_and_pagination(client):
    for index, (env, crit) in enumerate(
        [("production", "critical"), ("production", "low"), ("staging", "high")]
    ):
        client.post(
            "/servers",
            json=server_payload(
                name=f"Servidor {index}", hostname=f"srv-{index}", environment=env, criticality=crit
            ),
        )
    page = client.get(
        "/servers", params={"environment": "production", "sort": "criticality", "direction": "desc"}
    ).json()["data"]
    assert page["total"] == 2
    assert [item["criticality"] for item in page["items"]] == ["critical", "low"]

    paged = client.get("/servers", params={"page": 2, "page_size": 2}).json()["data"]
    assert paged["total"] == 3
    assert len(paged["items"]) == 1

    assert client.get("/servers", params={"q": "SRV-2"}).json()["data"]["total"] == 1
    assert client.get("/servers", params={"page_size": 500}).status_code == 422
    assert client.get("/servers", params={"sort": "uptime"}).status_code == 422


def test_invalid_path_id_is_rejected(client):
    assert client.get("/servers/not-a-uuid").status_code == 422


def test_not_found_uses_error_envelope(client):
    response = client.get("/servers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["data"]["error"]["code"] == "server_not_found"
    assert response.json()["meta"] == {"operationId": "get_it_server"}


def test_full_server_flow_over_http(client):
    server = client.post("/servers", json=server_payload()).json()["data"]
    sid = server["id"]
    edited = client.put(
        f"/servers/{sid}", json={**server_payload(criticality="high"), "revision": 1}
    )
    assert edited.status_code == 200
    assert edited.json()["data"]["revision"] == 2

    stale = client.put(f"/servers/{sid}", json={**server_payload(name="X"), "revision": 1})
    assert stale.status_code == 409

    client.post(f"/servers/{sid}/notes", json={"body": "Primeira nota."})
    client.post(f"/servers/{sid}/notes", json={"body": "Segunda nota."})
    notes = client.get(f"/servers/{sid}/notes").json()["data"]
    assert [n["body"] for n in notes] == ["Primeira nota.", "Segunda nota."]

    plan = client.post(
        f"/servers/{sid}/action-plans",
        json={"title": "Aplicar patch", "priority": "high", "due_date": "2026-11-01"},
    ).json()["data"]
    assert plan["is_overdue"] is True
    blocked = client.post(f"/servers/{sid}/archive", json={"revision": 2})
    assert blocked.status_code == 409

    done = client.post(
        f"/action-plans/{plan['id']}/status", json={"status": "done", "revision": 1}
    )
    assert done.json()["data"]["status"] == "done"
    archived = client.post(f"/servers/{sid}/archive", json={"revision": 2})
    assert archived.status_code == 200
    assert client.get("/servers").json()["data"]["total"] == 0
    assert client.get("/servers", params={"archived": "archived"}).json()["data"]["total"] == 1

    history = client.get(f"/servers/{sid}/history").json()["data"]
    assert history[0]["event_type"] == "server_archived"
    assert {event["event_type"] for event in history} >= {
        "server_created",
        "server_updated",
        "note_added",
        "action_plan_created",
        "action_plan_status_changed",
    }
