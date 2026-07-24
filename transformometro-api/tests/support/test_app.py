"""FastAPI de teste: mesmos routers, sem lifespan (migrations) e com JWT fake."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

# Env mínima antes de qualquer import que toque plugins DB.
for _key, _val in {
    "PLUGINS_DB_HOST": "127.0.0.1",
    "PLUGINS_DB_PORT": "5432",
    "PLUGINS_DB_NAME": "plugins_test",
    "PLUGINS_DB_USER": "test",
    "PLUGINS_DB_PASSWORD": "test",
}.items():
    os.environ.setdefault(_key, _val)

import tm_app.infrastructure.providers.database.plugins_postgres_connection as _pg_mod

_mock_conn = MagicMock()
_mock_conn.closed = False
_pg_mod.get_plugins_connection = lambda: _mock_conn  # type: ignore[assignment]
_pg_mod._cached_connection = _mock_conn

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from tm_app.core.responses import fail
from tm_app.interface.http.routes.collaboration_routes import router as collaboration_router
from tm_app.interface.http.routes.crud_routes import router as crud_router
from tm_app.interface.http.routes.dashboard_routes import router as dashboard_router
from tm_app.interface.http.routes.decomposition_routes import router as decomposition_router
from tm_app.interface.http.routes.diagram_routes import router as diagram_router
from tm_app.interface.http.routes.integrations_routes import router as integrations_router
from tm_app.interface.http.routes.json_backup_routes import router as json_backup_router
from tm_app.interface.http.routes.processo_arquivo_routes import router as processo_arquivo_router
from tm_app.interface.http.routes.revisao_evidence_routes import router as revisao_evidence_router
from tm_app.interface.http.routes.transformometro_routes import router as transformometro_router

TEST_USER = SimpleNamespace(
    id="test-user",
    sub="test-user",
    email="tm-test@delpi.local",
    name="TM Test",
    is_superadmin=True,
    permissions=[],
)


async def _fake_jwt_middleware(request: Request, call_next):
    request.state.user = TEST_USER
    return await call_next(request)


def create_test_app() -> FastAPI:
    app = FastAPI(title="Transformômetro API (test)", version="0.1.0-test")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        details = exc.errors()
        first = details[0] if details else {}
        loc = ".".join(str(part) for part in first.get("loc", []))
        msg = first.get("msg", "Dados inválidos.")
        message = f"{loc}: {msg}" if loc else msg
        return fail(message, 422)

    @app.get("/health", tags=["Health"], operation_id="health")
    def health():
        return {"status": "online", "service": "transformometro-api"}

    app.middleware("http")(_fake_jwt_middleware)
    app.include_router(transformometro_router)
    app.include_router(crud_router)
    app.include_router(dashboard_router)
    app.include_router(integrations_router)
    app.include_router(json_backup_router)
    app.include_router(revisao_evidence_router)
    app.include_router(processo_arquivo_router)
    app.include_router(diagram_router)
    app.include_router(decomposition_router)
    app.include_router(collaboration_router)
    return app
