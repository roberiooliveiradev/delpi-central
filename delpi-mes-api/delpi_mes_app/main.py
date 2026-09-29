import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware

from delpi_mes_app.composition.composer import close_gateway
from delpi_mes_app.config import settings
from delpi_mes_app.core.responses import fail
from delpi_mes_app.interface.http.routes.mes_routes import router as mes_router
from delpi_mes_app.middleware.auth_middleware import jwt_middleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_gateway()


app = FastAPI(
    title="Delpi MES API",
    description="BFF gerencial read-only do Delpi MES.",
    version="0.1.0",
    root_path=settings.API_ROOT_PATH,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", []))
    message = first.get("msg", "Dados inválidos.")
    return fail(f"{location}: {message}" if location else message, 422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception):
    logging.getLogger(__name__).exception("unhandled_exception")
    return fail("Erro interno do servidor.", 500)


app.middleware("http")(jwt_middleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/health", tags=["Health"], operation_id="get_delpi_mes_health")
def health():
    return {"status": "online", "service": "delpi-mes-api"}


app.include_router(mes_router)
