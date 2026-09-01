from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from production_pulse_app.config import settings
from production_pulse_app.core.responses import error, success
from production_pulse_app.interface.http.routes.catalog_routes import router as catalog_router
from production_pulse_app.interface.http.routes.device_routes import router as devices_router
from production_pulse_app.middleware.auth_middleware import jwt_middleware
from production_pulse_app.startup.register_device_drivers import register_device_drivers
from production_pulse_app.startup.run_migrations_on_startup import run_migrations_on_startup

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations_on_startup()
    register_device_drivers()
    yield
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        close_plugins_connection,
    )

    close_plugins_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Production Pulse API",
        version="0.2.0",
        root_path=settings.PRODUCTION_PULSE_API_ROOT_PATH,
        lifespan=lifespan,
    )
    app.middleware("http")(jwt_middleware)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        details = exc.errors()
        first = details[0] if details else {}
        loc = ".".join(str(part) for part in first.get("loc", []))
        msg = first.get("msg", "Dados inválidos.")
        message = f"{loc}: {msg}" if loc else msg
        payload = error(message, code="validation_error", status_code=422)
        status_code = payload.pop("_status_code", 422)
        return JSONResponse(status_code=status_code, content=payload)

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

    app.include_router(devices_router)
    app.include_router(catalog_router)
    return app


app = create_app()
