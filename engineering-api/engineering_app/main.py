import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from delpi_auth.credential_guard import check_credentials
from engineering_app.config import settings
from engineering_app.core.responses import fail
from engineering_app.interface.http.routes.health_routes import (
    router as health_router,
)
from engineering_app.interface.http.routes.overview_routes import (
    router as overview_router,
)
from engineering_app.interface.http.routes.home_routes import (
    router as home_router,
)
from engineering_app.interface.http.routes.lmp_routes import (
    router as lmp_router,
)
from engineering_app.interface.http.routes.product_routes import (
    router as product_router,
)
from engineering_app.interface.mcp import (
    combine_lifespan,
    mcp_http_app,
    mcp_metadata_router,
    mcp_mount_path_middleware,
)
from engineering_app.middleware.auth_middleware import jwt_middleware
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
    request_observability_middleware,
)

logging.basicConfig(
    level=settings.resolved_log_level(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    missing = settings.missing_auth_envs()
    if missing:
        raise RuntimeError(
            "engineering-api auth configuration incomplete — missing required envs: "
            + ", ".join(missing)
        )
    check_credentials()
    logger.info(
        "engineering_api_started service=%s env=%s root_path=%s",
        settings.SERVICE_NAME,
        settings.APP_ENV,
        settings.ENGINEERING_API_ROOT_PATH,
    )
    yield


app = FastAPI(
    title="Engineering API",
    description="BFF/composição do Portal Engenharia — bootstrap F1.S1.",
    version="0.1.0",
    root_path=settings.ENGINEERING_API_ROOT_PATH,
    lifespan=combine_lifespan(lifespan, mcp_http_app),
    docs_url=None,
    redoc_url=None,
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
    logging.getLogger(__name__).exception(
        "unhandled_exception request_id=%s", get_request_id()
    )
    return fail("Erro interno do servidor.", 500)


# Ordem: o último middleware registrado roda primeiro (convenção api-delpi).
# Observability envolve o JWT para instrumentar também 401/403/503 de auth.
app.middleware("http")(jwt_middleware)
app.middleware("http")(request_observability_middleware)
# Last registered http middleware runs first: rewrite /mcp → /mcp/
# antes do 307 do Mount (convenção dos demais MCPs da plataforma).
app.middleware("http")(mcp_mount_path_middleware)


app.include_router(health_router)
app.include_router(mcp_metadata_router)
app.include_router(home_router)
app.include_router(overview_router)
app.include_router(lmp_router)
app.include_router(product_router)

# Streamable HTTP MCP (path público: /apps/engineering-api/mcp) —
# AuthN/AuthZ via jwt_middleware (transporte OAuth + delpi_auth).
app.mount("/mcp", mcp_http_app)
