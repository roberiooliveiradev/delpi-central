from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from production_pulse_app.config import settings
from production_pulse_app.core.responses import error, success
from production_pulse_app.middleware.auth_middleware import AuthMiddleware
from production_pulse_app.startup.run_migrations_on_startup import run_migrations_on_startup

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations_on_startup()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Production Pulse API",
        version="0.1.0",
        root_path=settings.PRODUCTION_PULSE_API_ROOT_PATH,
        lifespan=lifespan,
    )
    app.add_middleware(AuthMiddleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        payload = error("Erro interno do servidor.", code="internal_error", status_code=500)
        status_code = payload.pop("_status_code", 500)
        return JSONResponse(status_code=status_code, content=payload)

    @app.get("/health")
    async def health():
        return success(
            {
                "service": "production-pulse-api",
                "status": "ok",
            }
        )

    return app


app = create_app()
