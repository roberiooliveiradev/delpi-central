import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from delpi_auth.cors_policy import build_allowed_origins
from maint_app.config import settings
from maint_app.core.responses import fail
from maint_app.interface.http.routes.filial_routes import router as filial_router
from maint_app.interface.http.routes.maintenance_routes import router as maintenance_router
from maint_app.interface.http.routes.mini_applicators_routes import router as mini_applicators_router
from maint_app.interface.http.routes.programas_maquinas_routes import (
    router as programas_maquinas_router,
)
from maint_app.interface.http.routes.operational_routes import router as operational_router
from maint_app.interface.http.routes.preventiva_routes import router as preventiva_router
from maint_app.middleware.auth_middleware import jwt_middleware
from maint_app.startup.run_migrations_on_startup import run_migrations_on_startup

logging.basicConfig(
    level=getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


ALLOWED_ORIGINS = build_allowed_origins(
    public_base_url=settings.PUBLIC_BASE_URL,
    keycloak_url=settings.VITE_KC_URL,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    try:
        yield
    finally:
        from maint_app.infrastructure.providers.database.plugins_postgres_connection import (
            close_plugins_connection,
        )

        close_plugins_connection()


app = FastAPI(
    title="Manutenção API",
    description="API do módulo Manutenção — mini-aplicadores e extensões futuras.",
    version="0.1.0",
    root_path=settings.MAINT_API_ROOT_PATH,
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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "online", "service": "maintenance-api"}


app.include_router(maintenance_router)
app.include_router(filial_router)
app.include_router(mini_applicators_router)
app.include_router(programas_maquinas_router)
app.include_router(operational_router)
app.include_router(preventiva_router)
