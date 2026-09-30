from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from bpmn_modeler.application.errors import (
    CONFLICT,
    INFRASTRUCTURE_FAILURE,
    INPUT_REJECTED_SECURITY,
    INVALID_DISPLAY_NAME,
    MODEL_ARCHIVED,
    MODEL_NOT_FOUND,
    NO_CHANGES,
    OUTCOME_VERIFICATION_FAILED,
    REVISION_NOT_FOUND,
    UNAUTHORIZED_OPERATION,
    VALIDATION_BLOCKED,
    ApplicationError,
)
from bpmn_modeler.application.use_cases import BpmnModelerService
from bpmn_modeler.infrastructure.persistence.connection import check_connection
from bpmn_modeler.infrastructure.persistence.migrations_runner import SCHEMA_NAME
from bpmn_modeler.infrastructure.persistence.repository import PostgresModelRepository
from bpmn_modeler.infrastructure.runtime import SystemClock, UuidGenerator
from bpmn_modeler.infrastructure.validation.blank import (
    TemplateBlankArtifactFactory,
)
from bpmn_modeler.infrastructure.validation.engine import LxmlBpmnValidator

from .auth import auth_middleware
from .responses import error_response
from .routes import router

logger = logging.getLogger(__name__)

ERROR_STATUS = {
    MODEL_NOT_FOUND: 404,
    REVISION_NOT_FOUND: 404,
    "REVISION_OWNERSHIP_MISMATCH": 404,
    MODEL_ARCHIVED: 409,
    NO_CHANGES: 409,
    INVALID_DISPLAY_NAME: 422,
    VALIDATION_BLOCKED: 422,
    CONFLICT: 412,
    INPUT_REJECTED_SECURITY: 400,
    UNAUTHORIZED_OPERATION: 403,
    OUTCOME_VERIFICATION_FAILED: 500,
    INFRASTRUCTURE_FAILURE: 503,
    "PRECONDITION_REQUIRED": 428,
    "INVALID_REQUEST": 400,
    "PAYLOAD_TOO_LARGE": 413,
    "UNAUTHORIZED": 401,
}

_RECOVERABLE = {CONFLICT, "RATE_LIMITED"}

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _serialize_details(details: dict) -> dict:
    serialized = {}
    for key, value in details.items():
        if hasattr(value, "model_dump"):
            serialized[key] = value.model_dump(mode="json")
        elif hasattr(value, "value") and hasattr(value, "name"):
            serialized[key] = value.value
        elif hasattr(value, "issues"):
            from .schemas import report_response

            serialized[key] = report_response(value).model_dump(mode="json")
        else:
            serialized[key] = value
    return serialized


def create_app(service: BpmnModelerService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.service is None:
            from bpmn_modeler.main import startup_env_check
            from bpmn_modeler.infrastructure.persistence.run_migrations_on_startup import (
                run_migrations_on_startup,
            )

            startup_env_check()
            run_migrations_on_startup()
            validator = LxmlBpmnValidator()  # fail-closed on bundle failure
            app.state.service = BpmnModelerService(
                repository=PostgresModelRepository(),
                validator=validator,
                input_safety=validator,
                blank_artifacts=TemplateBlankArtifactFactory(UuidGenerator()),
                clock=SystemClock(),
                ids=UuidGenerator(),
            )
        yield

    app = FastAPI(
        title="BPMN Modeler API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
        servers=[{"url": "/apps/bpmn-modeler-api"}],
    )
    app.state.service = service
    app.state.readiness = _readiness

    app.middleware("http")(auth_middleware)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request.state.request_id = (
            incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        status = ERROR_STATUS.get(exc.code, 500)
        code = exc.code
        if code == "REVISION_OWNERSHIP_MISMATCH":
            code = REVISION_NOT_FOUND
        return error_response(
            status,
            code,
            exc.message or "Erro na operação.",
            getattr(request.state, "request_id", "-"),
            recoverable=exc.code in _RECOVERABLE,
            details=_serialize_details(exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return error_response(
            422,
            "INVALID_REQUEST",
            "Requisição inválida.",
            getattr(request.state, "request_id", "-"),
            details={"issues": exc.errors()},
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        return error_response(
            401, "UNAUTHORIZED", "Autenticação necessária.",
            getattr(request.state, "request_id", "-"),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("unhandled_error path=%s", request.url.path)
        return error_response(
            503,
            INFRASTRUCTURE_FAILURE,
            "Falha de infraestrutura.",
            getattr(request.state, "request_id", "-"),
        )

    app.include_router(router)
    _patch_openapi(app)
    return app


def _patch_openapi(app: FastAPI) -> None:
    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            servers=app.servers,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "bearerAuth"
        ] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        for path, operations in schema.get("paths", {}).items():
            for method, operation in operations.items():
                if not isinstance(operation, dict):
                    continue
                if path in ("/health", "/ready"):
                    operation["security"] = []
                else:
                    operation["security"] = [{"bearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


def _readiness() -> dict[str, bool]:
    checks = {"database": False, "xsd_bundle": False, "schema": False}
    try:
        LxmlBpmnValidator()
        checks["xsd_bundle"] = True
    except Exception:
        pass
    try:
        checks["database"] = check_connection()
    except Exception:
        pass
    if checks["database"]:
        try:
            from bpmn_modeler.infrastructure.persistence.connection import (
                db_connection,
            )

            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT to_regclass('{SCHEMA_NAME}.models') AS m, "
                        f"to_regclass('{SCHEMA_NAME}.revisions') AS r"
                    )
                    row = cur.fetchone()
                conn.rollback()
            checks["schema"] = bool(row and row["m"] and row["r"])
        except Exception:
            pass
    return checks
