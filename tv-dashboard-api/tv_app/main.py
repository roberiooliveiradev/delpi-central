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
from tv_app.interface.http.routes.content_routes import router as content_router
from tv_app.interface.http.routes.native_screen_routes import router as native_screen_router
from tv_app.interface.http.routes.playlist_routes import router as playlist_router
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
    yield


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
app.include_router(slide_router)
app.include_router(content_router)
app.include_router(native_screen_router)
app.include_router(public_router)
