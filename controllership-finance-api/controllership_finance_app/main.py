import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from delpi_auth.cors_policy import build_allowed_origins
from controllership_finance_app.config import settings
from controllership_finance_app.core.responses import fail
from controllership_finance_app.interface.http.routes.admin_catalogs_routes import (
    router as admin_catalogs_router,
)
from controllership_finance_app.interface.http.routes.admin_checklist_routes import (
    router as admin_checklist_router,
)
from controllership_finance_app.interface.http.routes.clara_consent_routes import (
    router as clara_consent_router,
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
from controllership_finance_app.interface.http.routes.participants_routes import (  # noqa: E501
    router as participants_router,
)
from controllership_finance_app.interface.http.routes.health_routes import (
    router as health_router,
)
from controllership_finance_app.interface.http.routes.me_routes import (
    router as me_router,
)
from controllership_finance_app.interface.http.routes.packages_routes import (
    router as packages_router,
)
from controllership_finance_app.interface.http.routes.p3_routes import (
    router as p3_router,
)
from controllership_finance_app.interface.http.routes.pendencies_routes import (
    router as pendencies_router,
)
from controllership_finance_app.interface.http.routes.reports_routes import (
    router as reports_router,
)
from controllership_finance_app.interface.http.routes.validations_routes import (
    router as validations_router,
)
from controllership_finance_app.interface.http.routes.viewer_context_routes import (
    router as viewer_context_router,
)
from controllership_finance_app.interface.mcp import (
    combine_lifespan,
    mcp_http_app,
    mcp_metadata_router,
    mcp_mount_path_middleware,
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
    pollers: list[asyncio.Task] = []
    if settings.CF_NOTIFICATION_DISPATCH_ENABLED not in ("0", "false"):
        # R-105-05: recuperação da outbox sem nova ação do usuário —
        # mesmo padrão dos pollers de cipa/purchase-requests.
        from controllership_finance_app.startup.notification_dispatch_job import (
            run_closing_notification_dispatch_loop,
        )

        pollers.append(
            asyncio.create_task(
                run_closing_notification_dispatch_loop()
            )
        )
    try:
        yield
    finally:
        for poller in pollers:
            poller.cancel()
            with suppress(asyncio.CancelledError):
                await poller


app = FastAPI(
    title="Controllership & Finance API",
    description="BFF do Portal Controladoria & Finanças — fundação IMP-F0.",
    version="0.1.0",
    root_path=settings.CONTROLLERSHIP_FINANCE_API_ROOT_PATH,
    lifespan=combine_lifespan(lifespan, mcp_http_app),
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
# Último middleware registrado roda primeiro: reescreve /mcp → /mcp/
# antes do Mount 307 (mesmo padrão dos especialistas TÉO/VISTA/DAVI).
app.middleware("http")(mcp_mount_path_middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_metadata_router)
app.include_router(health_router)
app.include_router(viewer_context_router)
app.include_router(closing_router)
app.include_router(competences_router)
app.include_router(documents_router)
app.include_router(participants_router)
app.include_router(validations_router)
app.include_router(pendencies_router)
app.include_router(p3_router)
app.include_router(packages_router)
app.include_router(reports_router)
app.include_router(me_router)
app.include_router(admin_checklist_router)
app.include_router(admin_catalogs_router)
app.include_router(clara_consent_router)

# Streamable HTTP MCP — CLARA (external path:
# /apps/controllership-finance-api/mcp). Auth via jwt_middleware com
# gate de transporte MCP (service tokens proibidos; audience/scopes
# exatos; AuthZ de negócio permanece nas tools/BFF).
app.mount("/mcp", mcp_http_app)
