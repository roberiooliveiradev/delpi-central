import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from delpi_auth.credential_guard import check_credentials
from delpi_auth.cors_policy import build_allowed_origins
from controllership_finance_app.application.invoice_posting.change_notifier import (
    configure_invoice_posting_realtime,
    lnf_realtime_should_mount,
)
from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.invoice_posting.access_log_redaction import (
    install_token_redaction_filter,
)
from controllership_finance_app.core.responses import fail
from controllership_finance_app.interface.http.routes.admin_catalogs_routes import (
    router as admin_catalogs_router,
)
from controllership_finance_app.interface.http.routes.admin_checklist_routes import (
    router as admin_checklist_router,
)
from controllership_finance_app.interface.http.routes.analysis_routes import (
    router as analysis_router,
)
from controllership_finance_app.interface.http.routes.characters_routes import (
    router as characters_router,
)
from controllership_finance_app.interface.http.routes.clara_consent_routes import (
    router as clara_consent_router,
)
from controllership_finance_app.interface.http.routes.closing_routes import (
    router as closing_router,
)
from controllership_finance_app.interface.http.routes.closing_state_routes import (
    router as closing_state_router,
)
from controllership_finance_app.interface.http.routes.billing_mod_breakdown_routes import (
    router as billing_mod_breakdown_router,
)
from controllership_finance_app.interface.http.routes.production_order_consumption_routes import (
    router as production_order_consumption_router,
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
from controllership_finance_app.interface.http.routes.received_documents_routes import (  # noqa: E501
    router as received_documents_router,
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
install_token_redaction_filter()
_lnf_realtime_mounted = configure_invoice_posting_realtime(
    enabled=lnf_realtime_should_mount(
        hosted=settings.LNF_HOSTED_ENABLED,
        realtime=settings.LNF_REALTIME_ENABLED,
    )
)


ALLOWED_ORIGINS = build_allowed_origins(
    public_base_url=settings.PUBLIC_BASE_URL,
    keycloak_url=settings.VITE_KC_URL,
)


def _is_lnf_path(request: Request) -> bool:
    return "/lancamento-notas-fiscais" in (request.url.path or "")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    if settings.LNF_HOSTED_ENABLED:
        mode = settings.LNF_MIGRATIONS_MODE
        if mode not in ("verify", "apply"):
            raise RuntimeError(
                "LNF_MIGRATIONS_MODE deve ser 'verify' ou 'apply' "
                f"(recebido={mode!r})"
            )
        from controllership_finance_app.infrastructure.invoice_posting.migrations_verify import (
            apply_lnf_migrations,
            verify_lnf_migrations,
        )

        if mode == "apply":
            apply_lnf_migrations()
        else:
            verify_lnf_migrations()
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
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if settings.LNF_HOSTED_ENABLED and _is_lnf_path(request):
        from controllership_finance_app.interface.http.routes.invoice_posting.responses import (
            error_response,
        )

        return error_response(
            "Parâmetros inválidos",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    details = exc.errors()
    first = details[0] if details else {}
    loc = ".".join(str(part) for part in first.get("loc", []))
    msg = first.get("msg", "Dados inválidos.")
    message = f"{loc}: {msg}" if loc else msg
    return fail(message, 422)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if settings.LNF_HOSTED_ENABLED and _is_lnf_path(request):
        from controllership_finance_app.interface.http.routes.invoice_posting.responses import (
            error_response,
            not_found_response,
        )

        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        if exc.status_code == 404:
            return not_found_response(detail or "Recurso não encontrado")
        typed_code = getattr(exc, "error_code", None)
        if typed_code:
            code = typed_code
        else:
            code = "VALIDATION_ERROR" if exc.status_code == 422 else "HTTP_ERROR"
        return error_response(detail, status_code=exc.status_code, code=code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("unhandled_exception")
    if settings.LNF_HOSTED_ENABLED and _is_lnf_path(request):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
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
app.include_router(characters_router)
app.include_router(viewer_context_router)
app.include_router(closing_router)
app.include_router(closing_state_router)
app.include_router(billing_mod_breakdown_router)
app.include_router(production_order_consumption_router)
app.include_router(analysis_router)
app.include_router(competences_router)
app.include_router(documents_router)
app.include_router(participants_router)
app.include_router(validations_router)
app.include_router(pendencies_router)
app.include_router(p3_router)
app.include_router(packages_router)
app.include_router(received_documents_router)
app.include_router(reports_router)
app.include_router(me_router)
app.include_router(admin_checklist_router)
app.include_router(admin_catalogs_router)
app.include_router(clara_consent_router)

# LNF (invoice_posting) — dark by default; mount only when flagged.
if settings.LNF_HOSTED_ENABLED:
    from controllership_finance_app.interface.http.routes.invoice_posting.router import (
        router as invoice_posting_router,
    )

    app.include_router(invoice_posting_router)
    if _lnf_realtime_mounted:
        from controllership_finance_app.interface.http.routes.invoice_posting.realtime_routes import (
            router as invoice_posting_realtime_router,
        )

        app.include_router(invoice_posting_realtime_router)

# Streamable HTTP MCP — CLARA (external path:
# /apps/controllership-finance-api/mcp). Auth via jwt_middleware com
# gate de transporte MCP (service tokens proibidos; audience/scopes
# exatos; AuthZ de negócio permanece nas tools/BFF).
app.mount("/mcp", mcp_http_app)
