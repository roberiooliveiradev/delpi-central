import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi

from delpi_auth.cors_policy import build_allowed_origins
from delpi_auth.credential_guard import check_credentials

from it_portal_app.config import settings
from it_portal_app.core.responses import fail
from it_portal_app.domain.errors import DomainError
from it_portal_app.interface.http.routes.action_plans_routes import (
    router as action_plans_router,
)
from it_portal_app.interface.http.routes.host_services_routes import router as host_services_router
from it_portal_app.interface.http.routes.collector_routes import (
    router as collector_router,
)
from it_portal_app.interface.http.routes.overview_routes import (
    router as overview_router,
)
from it_portal_app.interface.http.routes.database_routes import (
    router as database_router,
)
from it_portal_app.interface.http.routes.integration_routes import (
    router as integration_router,
)
from it_portal_app.interface.http.routes.network_routes import (
    router as network_router,
)
from it_portal_app.interface.http.routes.servers_routes import (
    router as servers_router,
)
from it_portal_app.interface.http.routes.services_routes import (
    router as services_router,
)
from it_portal_app.interface.http.s2s_auth import S2SHttpException
from it_portal_app.middleware.auth_middleware import jwt_middleware
from it_portal_app.observability import configure_logging, request_context_middleware
from it_portal_app.startup.run_migrations_on_startup import run_migrations_on_startup

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = build_allowed_origins(
    public_base_url=settings.PUBLIC_BASE_URL,
    keycloak_url=settings.VITE_KC_URL,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials(extra_vars=["IT_PORTAL_DB_PASSWORD"])
    run_migrations_on_startup()
    yield


app = FastAPI(
    title="IT Portal API",
    description=(
        "BFF do Portal de TI DELPI — inventário de servidores, notas técnicas, "
        "planos de ação, serviços/aplicações, bancos, redes, integrações e "
        "observações automáticas. Rotas humanas exigem JWT Keycloak e "
        "permissões do Core; ingestão do coletor usa S2S individual."
    ),
    version="0.4.0",
    root_path=settings.IT_PORTAL_API_ROOT_PATH,
    lifespan=lifespan,
    redirect_slashes=False,
)


def _operation_id(request: Request) -> str | None:
    route = request.scope.get("route")
    return getattr(route, "operation_id", None)


@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    if exc.status >= 500:
        logger.error(
            "it_portal_persistence_unavailable",
            extra={"fields": {"code": exc.code, "operation_id": _operation_id(request)}},
        )
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code, "details": exc.details or None}},
        operation_id=_operation_id(request),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part not in ("body", "query", "path")]
        fields[".".join(location) or "request"] = error.get("msg", "Valor inválido.")
    return fail(
        "Dados inválidos.",
        422,
        data={"error": {"code": "invalid_request", "details": {"fields": fields}}},
        operation_id=_operation_id(request),
    )


@app.exception_handler(S2SHttpException)
async def s2s_exception_handler(request: Request, exc: S2SHttpException):
    return fail(
        exc.detail if isinstance(exc.detail, str) else "Forbidden",
        exc.status_code,
        data={"error": {"code": exc.error_code, "details": None}},
        operation_id=_operation_id(request),
    )


app.middleware("http")(jwt_middleware)
app.middleware("http")(request_context_middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview_router)
app.include_router(servers_router)
app.include_router(action_plans_router)
app.include_router(services_router)
app.include_router(database_router)
app.include_router(network_router)
app.include_router(integration_router)
app.include_router(collector_router)
app.include_router(host_services_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path, operations in schema.get("paths", {}).items():
        if path == "/health":
            continue
        for operation in operations.values():
            operation["security"] = [{"bearerAuth": []}]
    schema["servers"] = [{"url": settings.IT_PORTAL_API_ROOT_PATH}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
