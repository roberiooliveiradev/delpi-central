import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from production_control_app.middleware.auth_middleware import jwt_middleware

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.config import settings
from production_control_app.core.responses import fail
from production_control_app.interface.http.routes.delivery_map_routes import (
    router as delivery_map_router,
)
from production_control_app.interface.http.routes.demand_routes import router as demand_router
from production_control_app.interface.http.routes.materials_routes import router as materials_router
from production_control_app.interface.http.routes.machine_load_routes import (
    router as machine_load_router,
)
from production_control_app.interface.http.routes.overview_routes import router as overview_router
from production_control_app.interface.http.routes.public_machine_load_routes import (
    router as public_machine_load_router,
)
from production_control_app.interface.http.routes.public_delivery_map_routes import (
    router as public_delivery_map_router,
)
from production_control_app.interface.http.routes.problem_analysis_routes import (
    router as problem_analysis_router,
)
from production_control_app.interface.http.routes.subplugin_routes import router as subplugin_router
from production_control_app.startup.run_migrations_on_startup import run_migrations_on_startup

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
    api_env = os.getenv("API_DELPI_ENV", "development")
    if api_env != "production":
        origins.add("http://localhost")
    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations_on_startup()
    machine_load_realtime_hub.bind_loop(asyncio.get_running_loop())
    worker = asyncio.create_task(machine_load_realtime_hub.worker())
    try:
        yield
    finally:
        worker.cancel()


app = FastAPI(
    title="Portal PCP API",
    description="BFF do Portal PCP — catálogo de subplugins e análise de problemas via api-delpi.",
    version="0.1.0",
    root_path=settings.PC_API_ROOT_PATH,
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
    return {"status": "online", "service": "production-control-api"}


app.include_router(subplugin_router)
app.include_router(overview_router)
app.include_router(machine_load_router)
app.include_router(public_machine_load_router)
app.include_router(public_delivery_map_router)
app.include_router(problem_analysis_router)
app.include_router(demand_router)
app.include_router(materials_router)
app.include_router(delivery_map_router)
