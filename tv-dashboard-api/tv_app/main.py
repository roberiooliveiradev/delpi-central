import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from delpi_auth.credential_guard import check_credentials
from tv_app.config import settings
from tv_app.core.responses import fail
from tv_app.interface.http.routes.data_api_routes import router as data_api_router
from tv_app.interface.http.routes.data_routes import router as data_routes_router
from tv_app.interface.http.routes.content_routes import router as content_router
from tv_app.interface.http.routes.media_routes import router as media_router
from tv_app.interface.http.routes.native_screen_routes import router as native_screen_router
from tv_app.application.services.presentation_realtime_hub import presentation_realtime_hub
from tv_app.interface.http.routes.playlist_history_routes import router as playlist_history_router
from tv_app.interface.http.routes.playlist_routes import router as playlist_router
from tv_app.interface.http.routes.presentation_realtime_routes import router as presentation_realtime_router
from tv_app.interface.http.routes.public_routes import router as public_router
from tv_app.interface.http.routes.slide_routes import router as slide_router
from tv_app.middleware.auth_middleware import jwt_middleware
from tv_app.startup.run_migrations_on_startup import run_migrations_on_startup

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
    if settings.TV_OPENAPI_SYNC_ON_STARTUP:
        from tv_app.application.services.tv_openapi_catalog_sync_service import (
            TvOpenApiCatalogSyncService,
        )

        report = await asyncio.to_thread(TvOpenApiCatalogSyncService().sync_safe)
        if report.get("ok"):
            logging.getLogger(__name__).info(
                "OpenAPI TV sync ok: %s rotas",
                report.get("routesWritten"),
            )
        else:
            logging.getLogger(__name__).warning(
                "OpenAPI TV sync skip: %s",
                report.get("error"),
            )
    loop = asyncio.get_running_loop()
    presentation_realtime_hub.bind_loop(loop)
    worker = asyncio.create_task(presentation_realtime_hub.worker())
    try:
        yield
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


app = FastAPI(
    title="TV Dashboard API",
    description="API do módulo Painéis TV — programações rotativas para displays corporativos.",
    version="0.1.0",
    root_path=settings.TV_DASHBOARD_API_ROOT_PATH,
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
    return {"status": "online", "service": "tv-dashboard-api"}


app.include_router(playlist_router)
app.include_router(playlist_history_router)
app.include_router(slide_router)
app.include_router(media_router)
app.include_router(content_router)
app.include_router(native_screen_router)
app.include_router(data_routes_router)
app.include_router(data_api_router)
app.include_router(public_router)
app.include_router(presentation_realtime_router)
