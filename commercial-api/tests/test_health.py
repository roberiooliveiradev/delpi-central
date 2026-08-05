from unittest.mock import patch

from fastapi.testclient import TestClient

from commercial_app.main import app


def test_root_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["service"] == "commercial-api"


@patch(
    "commercial_app.infrastructure.persistence.plugins.plugin_base_repository.PluginBaseRepository"
)
def test_ready_endpoint(mock_repo):
    mock_repo.return_value.fetch_one.return_value = {
        "migrations_table": "commercial.schema_migrations",
    }
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "commercial-api"
    assert payload["db_ready"] is True
