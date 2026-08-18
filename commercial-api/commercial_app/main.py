import logging
import os
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from commercial_app.config import settings
from commercial_app.core.responses import fail
from commercial_app.application.services.commercial_realtime_hub import (
    commercial_realtime_hub,
)
from commercial_app.interface.http.routes.realtime_routes import router as realtime_router
from commercial_app.interface.http.routes.attachment_routes import router as attachment_router
from commercial_app.interface.http.routes.analytics_routes import router as analytics_router
from commercial_app.interface.http.routes.customer_routes import router as customer_router
from commercial_app.interface.http.routes.open_orders_routes import (
    router as open_orders_router,
)
from commercial_app.interface.http.routes.production_bff_routes import (
    router as production_bff_router,
)
from commercial_app.interface.http.routes.proposal_documents_routes import (
    router as proposal_documents_router,
)
from commercial_app.interface.http.routes.seller_portfolio_routes import (
    router as seller_portfolio_router,
)
from commercial_app.interface.http.routes.home_favorites_routes import (
    router as home_favorites_router,
)
from commercial_app.interface.http.routes.forecast_routes import (
    router as forecast_router,
)
from commercial_app.interface.http.routes.settings_routes import (
    router as settings_router,
)
from commercial_app.interface.http.routes.worklist_routes import (
    activities_router,
    me_router as worklist_me_router,
    tasks_router,
)
from commercial_app.interface.http.routes.user_profile_routes import (
    router as user_profile_router,
)
from commercial_app.interface.http.routes.group_routes import (
    router as group_router,
)
from commercial_app.interface.http.routes.administration_routes import (
    router as administration_router,
)
from commercial_app.interface.http.routes.integration_jobs_routes import (
    router as integration_jobs_router,
)
from commercial_app.middleware.auth_middleware import jwt_middleware
from commercial_app.startup.run_migrations_on_startup import run_migrations_on_startup

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
    check_credentials()
    run_migrations_on_startup()
    loop = asyncio.get_running_loop()
    commercial_realtime_hub.bind_loop(loop)
    worker = asyncio.create_task(commercial_realtime_hub.worker())
    try:
        yield
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker
        from commercial_app.infrastructure.providers.database.plugins_postgres_connection import (
            close_plugins_connection,
        )

        close_plugins_connection()


app = FastAPI(
    title="Commercial API",
    description="API do módulo Comercial — carteiras, avatars e extensões futuras.",
    version="0.1.0",
    root_path=settings.COMMERCIAL_API_ROOT_PATH,
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
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], operation_id="get_commercial_health")
def health():
    return {"status": "online", "service": "commercial-api"}


@app.get("/ready", tags=["Health"], operation_id="get_commercial_ready")
def ready():
    db_ready = False
    db_hint = None
    try:
        from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
            PluginBaseRepository,
        )

        row = PluginBaseRepository().fetch_one(
            """
            SELECT to_regclass('commercial.schema_migrations')::text AS migrations_table
            """
        )
        db_ready = bool(row and row.get("migrations_table"))
        if not db_ready:
            db_hint = (
                "Tabela commercial.schema_migrations não encontrada. "
                "Execute migrations ou habilite COMMERCIAL_RUN_MIGRATIONS_ON_STARTUP."
            )
    except Exception as exc:
        db_hint = str(exc)

    return {
        "status": "ready" if db_ready else "degraded",
        "service": "commercial-api",
        "db_ready": db_ready,
        "db_hint": db_hint,
    }


app.include_router(seller_portfolio_router)
app.include_router(customer_router)
app.include_router(open_orders_router)
app.include_router(analytics_router)
app.include_router(proposal_documents_router)
app.include_router(production_bff_router)
app.include_router(worklist_me_router)
app.include_router(home_favorites_router)
app.include_router(forecast_router)
app.include_router(settings_router)
app.include_router(tasks_router)
app.include_router(activities_router)
app.include_router(attachment_router)
app.include_router(user_profile_router)
app.include_router(group_router)
app.include_router(administration_router)
app.include_router(integration_jobs_router)
app.include_router(realtime_router)
