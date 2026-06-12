from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.main import app


def test_root_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["service"] == "maintenance-api"


@patch("maint_app.interface.http.routes.maintenance_routes.PluginBaseRepository")
def test_module_health(mock_repo):
    mock_repo.return_value.fetch_one.return_value = {"migrations_table": "maintenance.schema_migrations"}
    client = TestClient(app)
    response = client.get("/maintenance/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "maintenance"
    assert payload["db_ready"] is True
