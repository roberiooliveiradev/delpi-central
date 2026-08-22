import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from financial_app.config import settings
from financial_app.core.responses import fail
from financial_app.interface.http.routes.cost_center_routes import router as cost_center_router
from financial_app.interface.http.routes.delinquency_routes import router as delinquency_router
from financial_app.interface.http.routes.indicators_routes import router as indicators_router
from financial_app.interface.http.routes.overview_routes import router as overview_router
from financial_app.interface.http.routes.subplugin_routes import router as subplugin_router
from financial_app.middleware.auth_middleware import jwt_middleware
from financial_app.startup.run_migrations_on_startup import run_migrations_on_startup

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
    run_migrations_on_startup()
    yield


app = FastAPI(
    title="Portal Financeiro API",
    description=(
        "BFF do Portal Financeiro — gestão à vista, inadimplência, despesas por centro "
        "de custo e indicadores estratégicos do departamento Financeiro."
    ),
    version="0.1.0",
    root_path=settings.FIN_API_ROOT_PATH,
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
    return {"status": "online", "service": "financial-api"}


app.include_router(subplugin_router)
app.include_router(overview_router)
app.include_router(delinquency_router)
app.include_router(cost_center_router)
app.include_router(indicators_router)
