from production_pulse_app.application.services.device_poll_scheduler_service import (
    reset_device_poll_scheduler_for_tests,
)
from production_pulse_app.config import settings
from production_pulse_app.main import app


def test_health(monkeypatch):
    monkeypatch.setattr(settings, "PP_POLL_SCHEDULER_ENABLED", False)
    reset_device_poll_scheduler_for_tests()
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "production-pulse-api"
    assert body["data"]["status"] == "ok"
    assert body["data"]["scheduler"]["enabled"] is False
    assert body["data"]["scheduler"]["healthy"] is True
