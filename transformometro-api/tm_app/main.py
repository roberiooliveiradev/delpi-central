import logging
import os
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from delpi_auth.credential_guard import check_credentials
from tm_app.config import settings
from tm_app.core.errors import format_validation_error
from tm_app.core.responses import fail
from tm_app.middleware.auth_middleware import jwt_middleware
from tm_app.middleware.gpt_actions_error_envelope import (
    gpt_actions_error_envelope_middleware,
)
from tm_app.middleware.path_alias_middleware import path_alias_middleware
from tm_app.interface.http.routes.crud_routes import router as crud_router
from tm_app.interface.http.routes.dashboard_routes import router as dashboard_router
from tm_app.interface.http.routes.gpt_actions_routes import router as gpt_actions_router
from tm_app.interface.http.routes.integrations_routes import router as integrations_router
from tm_app.interface.http.routes.json_backup_routes import router as json_backup_router
from tm_app.interface.http.routes.collaboration_routes import router as collaboration_router
from tm_app.interface.http.routes.decomposition_routes import router as decomposition_router
from tm_app.interface.http.routes.diagram_routes import router as diagram_router
from tm_app.interface.http.routes.revision_evidence_routes import router as revision_evidence_router
from tm_app.interface.http.routes.process_file_routes import router as process_file_router
from tm_app.interface.http.routes.transformometro_routes import router as transformometro_router
from tm_app.interface.http.routes.meeting_minutes_routes import router as meeting_minutes_router
from tm_app.interface.http.routes.public_meeting_minutes_routes import public_router as public_meeting_minutes_router
from tm_app.interface.http.routes.signature_profile_routes import router as signature_profile_router
from tm_app.interface.http.routes.task_routes import router as task_router
from tm_app.interface.http.routes.interaction_room_routes import router as interaction_room_router
from tm_app.interface.http.routes.person_profile_routes import router as person_profile_router
from tm_app.application.services.transformometro_realtime_hub import (
    transformometro_realtime_hub,
)
from tm_app.interface.http.routes.realtime_routes import router as realtime_router
from tm_app.interface.mcp import (
    combine_lifespan,
    mcp_http_app,
    mcp_metadata_router,
    mcp_mount_path_middleware,
)
from tm_app.startup.run_migrations_on_startup import run_migrations_on_startup

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

    # localhost only in development
    api_env = os.getenv("API_DELPI_ENV", "development")
    if api_env != "production":
        origins.add("http://localhost")

    # Custom GPT Builder / Actions may preflight the public OpenAPI schema.
    origins.add("https://chatgpt.com")
    origins.add("https://chat.openai.com")
    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    loop = asyncio.get_running_loop()
    transformometro_realtime_hub.bind_loop(loop)
    worker = asyncio.create_task(transformometro_realtime_hub.worker())
    trace_poller = None
    if settings.TM_SIGN_INVITE_MAIL_TRACE_ENABLED:
        from tm_app.startup.sign_invite_mail_trace_job import (
            run_sign_invite_mail_trace_loop,
        )

        trace_poller = asyncio.create_task(run_sign_invite_mail_trace_loop())
    try:
        yield
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker
        if trace_poller is not None:
            trace_poller.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await trace_poller
        from tm_app.infrastructure.providers.database.plugins_postgres_connection import (
            close_plugins_connection,
        )

        close_plugins_connection()


app = FastAPI(
    title="Transformômetro API",
    description="API do Transformômetro — melhorias de processo e ROI.",
    version="0.1.0",
    root_path=settings.TM_API_ROOT_PATH,
    lifespan=combine_lifespan(lifespan, mcp_http_app),
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    message, data = format_validation_error(exc)
    data = {**data, "error_kind": "validation"}
    return fail(message, 422, data)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logging.getLogger(__name__).exception("unhandled_exception")
    return fail(
        "Erro interno do servidor.",
        500,
        {"error_kind": "internal", "error_type": type(exc).__name__},
    )


app.middleware("http")(gpt_actions_error_envelope_middleware)
app.middleware("http")(jwt_middleware)
app.middleware("http")(path_alias_middleware)
# Last registered http middleware runs first: rewrite /mcp → /mcp/ before Mount 307.
app.middleware("http")(mcp_mount_path_middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], operation_id="health")
def health():
    return {"status": "online", "service": "transformometro-api"}


app.include_router(mcp_metadata_router)
app.include_router(transformometro_router)
app.include_router(gpt_actions_router)
app.include_router(meeting_minutes_router, prefix="/transformometro/meeting-minutes")
app.include_router(meeting_minutes_router, prefix="/transformometro/atas")
app.include_router(public_meeting_minutes_router, prefix="/public/meeting-minutes/sign-invites")
app.include_router(public_meeting_minutes_router, prefix="/public/atas/sign-invites")
app.include_router(signature_profile_router)
app.include_router(task_router)
app.include_router(interaction_room_router)
app.include_router(person_profile_router)
app.include_router(crud_router)
app.include_router(dashboard_router)
app.include_router(integrations_router)
app.include_router(json_backup_router)
app.include_router(revision_evidence_router)
app.include_router(process_file_router)
app.include_router(diagram_router)
app.include_router(decomposition_router)
app.include_router(collaboration_router)
app.include_router(realtime_router)
# Streamable HTTP MCP (external path: /apps/transformometro-api/mcp). Auth via jwt_middleware.
app.mount("/mcp", mcp_http_app)
