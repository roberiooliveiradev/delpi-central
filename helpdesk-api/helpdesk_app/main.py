import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from delpi_auth.credential_guard import check_credentials
from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ticket_service import TicketService
from helpdesk_app.config import settings
from helpdesk_app.domain.errors import HelpdeskError
from helpdesk_app.infrastructure.crypto import TokenCipher
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from helpdesk_app.infrastructure.persistence.postgres import (
    PostgresIdempotencyStore,
    PostgresSessionStore,
    PostgresStateStore,
)
from helpdesk_app.interface.http.auth_routes import router as auth_router
from helpdesk_app.interface.http.ticket_routes import router as ticket_router
from helpdesk_app.middleware.auth_middleware import jwt_middleware
from helpdesk_app.startup.run_migrations_on_startup import run_migrations_on_startup

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


def build_runtime():
    cipher = TokenCipher(settings.HELPDESK_TOKEN_ENCRYPTION_KEY)
    glpi = HttpxGlpiClient(
        base_url=settings.GLPI_BASE_URL,
        client_id=settings.GLPI_OAUTH_CLIENT_ID,
        client_secret=settings.GLPI_OAUTH_CLIENT_SECRET,
        redirect_uri=settings.GLPI_OAUTH_REDIRECT_URI,
        connect_timeout=settings.GLPI_HTTP_CONNECT_TIMEOUT,
        read_timeout=settings.GLPI_HTTP_READ_TIMEOUT,
    )
    states = PostgresStateStore(cipher)
    sessions = PostgresSessionStore(cipher)
    oauth = OAuthService(glpi, states, sessions)
    tickets = TicketService(glpi, oauth, PostgresIdempotencyStore())
    return oauth, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    oauth, tickets = build_runtime()
    app.state.oauth = oauth
    app.state.tickets = tickets
    app.state.public_base_url = settings.PUBLIC_BASE_URL
    yield


app = FastAPI(
    title="Helpdesk API",
    description="BFF de Meus Chamados de TI. O GLPI permanece dono do chamado.",
    version="0.1.0",
    root_path=settings.HELPDESK_API_ROOT_PATH,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, _exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error"})


@app.exception_handler(HelpdeskError)
async def helpdesk_error_handler(_request: Request, exc: HelpdeskError):
    body = {"error": exc.code}
    if exc.code == "glpi_link_required":
        body["authorize_url"] = "/apps/helpdesk-api/auth/glpi/start"
    return JSONResponse(status_code=exc.status_code, content=body)


app.middleware("http")(jwt_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_origins() or ["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Location"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "online", "service": "helpdesk-api"}


app.include_router(auth_router)
app.include_router(ticket_router)
