from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_observability_middleware import request_observability_middleware


def test_request_observability_adds_headers_and_logs() -> None:
    app = FastAPI()

    @app.get("/engineering/lmps/dashboard/summary", operation_id="get_lmps_dashboard_summary")
    async def summary_route():
        return {"ok": True}

    app.middleware("http")(request_observability_middleware)

    with TestClient(app) as client:
        response = client.get("/engineering/lmps/dashboard/summary")

    assert response.status_code == 200
    assert response.headers["X-Operation-Id"] == "get_lmps_dashboard_summary"
    assert "X-Response-Time-Ms" in response.headers
