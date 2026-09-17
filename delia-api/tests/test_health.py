from app.application.health import (
    build_liveness_status,
    health_claims_unimplemented_dependency,
)


def test_health_returns_available_liveness(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body == {
        "status": "available",
        "service": "delia-api",
        "version": "0.0.1",
    }
    assert health_claims_unimplemented_dependency(body) is False


def test_health_does_not_claim_unimplemented_dependencies(client):
    body = client.get("/health").get_json()
    forbidden = {
        "database",
        "db",
        "core",
        "core_api",
        "domain",
        "llm",
        "provider",
        "providers",
        "automation_hub",
        "jwt",
        "ready",
        "dependencies",
    }
    assert forbidden.isdisjoint(set(body.keys()))


def test_liveness_builder_stays_process_scoped():
    payload = build_liveness_status(service_name="delia-api", service_version="9.9.9")
    assert payload["status"] == "available"
    assert payload["version"] == "9.9.9"
    assert "database" not in payload
