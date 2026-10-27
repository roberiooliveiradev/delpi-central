import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from engineering_app.config import settings
from engineering_app.core.responses import fail
from engineering_app.interface.http.routes.health_routes import (
    router as health_router,
)

logging.basicConfig(
    level=settings.resolved_log_level(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
    lifespan=lifespan,
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
    logging.getLogger(__name__).exception("unhandled_exception")
    return fail("Erro interno do servidor.", 500)


app.include_router(health_router)
