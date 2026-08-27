import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from purchase_requests_app.config import settings
from purchase_requests_app.core.responses import fail
from purchase_requests_app.interface.http.routes.portal_rbac_routes import (
    portal_rbac_router,
)
from purchase_requests_app.interface.http.routes.purchase_requests_routes import (
    admin_router,
    router as purchase_requests_router,
)
from purchase_requests_app.middleware.auth_middleware import jwt_middleware
from purchase_requests_app.startup.run_migrations_on_startup import run_migrations_on_startup

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
    if os.getenv("API_DELPI_ENV", "development") != "production":
        origins.add("http://localhost")
    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    pollers: list[asyncio.Task] = []
    if settings.PURCHASE_REQUESTS_PO_NOTIFICATIONS_ENABLED:
        from purchase_requests_app.startup.purchase_order_linked_notification_job import (
            run_purchase_order_linked_notification_loop,
        )
        from purchase_requests_app.startup.purchase_receipt_recorded_notification_job import (
            run_purchase_receipt_recorded_notification_loop,
        )

        pollers.append(asyncio.create_task(run_purchase_order_linked_notification_loop()))
        pollers.append(asyncio.create_task(run_purchase_receipt_recorded_notification_loop()))
    try:
        yield
    finally:
        for poller in pollers:
            poller.cancel()
            with suppress(asyncio.CancelledError):
                await poller
        from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
            close_plugins_connection,
        )

        close_plugins_connection()


app = FastAPI(
    title="Purchase Requests API",
    description="BFF do Painel de Solicitações de Compras.",
    version="0.1.0",
    root_path=settings.PURCHASE_REQUESTS_API_ROOT_PATH,
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
    return {"status": "online", "service": "purchase-requests-api"}


app.include_router(purchase_requests_router)
app.include_router(admin_router)
app.include_router(portal_rbac_router)
