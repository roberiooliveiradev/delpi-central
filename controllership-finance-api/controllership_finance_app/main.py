import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from delpi_auth.cors_policy import build_allowed_origins
from controllership_finance_app.config import settings
from controllership_finance_app.core.responses import fail
from controllership_finance_app.interface.http.routes.admin_checklist_routes import (
    router as admin_checklist_router,
)
from controllership_finance_app.interface.http.routes.closing_routes import (
    router as closing_router,
)
from controllership_finance_app.interface.http.routes.competences_routes import (
    router as competences_router,
)
from controllership_finance_app.interface.http.routes.documents_routes import (
    router as documents_router,
)
from controllership_finance_app.interface.http.routes.health_routes import (
    router as health_router,
)
from controllership_finance_app.interface.http.routes.validations_routes import (
    router as validations_router,
)
from controllership_finance_app.interface.http.routes.viewer_context_routes import (
    router as viewer_context_router,
)
from controllership_finance_app.middleware.auth_middleware import jwt_middleware
from controllership_finance_app.startup.run_migrations_on_startup import (
    run_migrations_on_startup,
)

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
    yield


app = FastAPI(
    title="Controllership & Finance API",
    description="BFF do Portal Controladoria & Finanças — fundação IMP-F0.",
    version="0.1.0",
    root_path=settings.CONTROLLERSHIP_FINANCE_API_ROOT_PATH,
    lifespan=lifespan,
    # Evita 307 slash-redirect com Location http:// atrás de TLS termination
    # (Mixed Content no browser). Clientes devem usar o path exato da rota.
    redirect_slashes=False,
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

app.include_router(health_router)
app.include_router(viewer_context_router)
app.include_router(closing_router)
app.include_router(competences_router)
app.include_router(documents_router)
app.include_router(validations_router)
app.include_router(admin_checklist_router)
