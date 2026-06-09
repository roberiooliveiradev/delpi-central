from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.observability.request_context import (
    bind_request_context,
    get_operation_id,
    reset_request_context,
)


def test_get_operation_id_lazy_resolve_during_handler() -> None:
    app = FastAPI()

    @app.middleware("http")
    async def bind_context_middleware(request, call_next):
        tokens = bind_request_context(request)
        try:
            return await call_next(request)
        finally:
            reset_request_context(tokens)

    @app.get("/quality/ppm/internal/summary", operation_id="get_ppm_internal_summary")
    def ppm_summary():
        assert get_operation_id() == "get_ppm_internal_summary"
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/quality/ppm/internal/summary")

    assert response.status_code == 200
