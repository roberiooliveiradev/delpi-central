import logging
import os
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from delpi_auth.credential_guard import check_credentials
from tm_app.config import settings
from tm_app.core.errors import format_api_error
from tm_app.core.responses import fail
from tm_app.interface.http.routes.crud_routes import router as crud_router
from tm_app.interface.http.routes.dashboard_routes import router as dashboard_router
from tm_app.interface.http.routes.integrations_routes import router as integrations_router
from tm_app.interface.http.routes.json_backup_routes import router as json_backup_router
from tm_app.interface.http.routes.collaboration_routes import router as collaboration_router
from tm_app.interface.http.routes.decomposition_routes import router as decomposition_router
from tm_app.interface.http.routes.diagram_routes import router as diagram_router
from tm_app.interface.http.routes.revisao_evidence_routes import router as revisao_evidence_router
from tm_app.interface.http.routes.processo_arquivo_routes import router as processo_arquivo_router
from tm_app.interface.http.routes.transformometro_routes import router as transformometro_router
from tm_app.application.services.transformometro_realtime_hub import (
    transformometro_realtime_hub,
)
from tm_app.interface.http.routes.realtime_routes import router as realtime_router
from tm_app.middleware.auth_middleware import jwt_middleware
from tm_app.startup.run_migrations_on_startup import run_migrations_on_startup

logging.basicConfig(
    level=getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def build_allowed_origins() -> list[str]:
    origins: set[str] = set()

    if settings.PUBLIC_BASE_URL:
        origins.add(settings.PUBLIC_BASE_URL.rstrip("/"))

    if settings.VITE_KC_URL:
        if "/auth" in settings.VITE_KC_URL:
            origins.add(settings.VITE_KC_URL.split("/auth")[0].rstrip("/"))
        else:
            origins.add(settings.VITE_KC_URL.rstrip("/"))

    # localhost only in development
    api_env = os.getenv("API_DELPI_ENV", "development")
    if api_env != "production":
        origins.add("http://localhost")
    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    loop = asyncio.get_running_loop()
    transformometro_realtime_hub.bind_loop(loop)
    worker = asyncio.create_task(transformometro_realtime_hub.worker())
    try:
        yield
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


app = FastAPI(
    title="Transformômetro API",
    description="API do Transformômetro — melhorias de processo e ROI.",
    version="0.1.0",
    root_path=settings.TM_API_ROOT_PATH,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    details = exc.errors()
    first = details[0] if details else {}
    loc = ".".join(str(part) for part in first.get("loc", []))
    msg = first.get("msg", "Dados inválidos.")
    message = f"{loc}: {msg}" if loc else msg
    return fail(message, 422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logging.getLogger(__name__).exception("unhandled_exception")
    return fail("Erro interno do servidor.", 500)


app.middleware("http")(jwt_middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "online", "service": "transformometro-api"}


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
app.include_router(realtime_router)
