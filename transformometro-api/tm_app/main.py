import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from tm_app.config import settings
from tm_app.interface.http.routes.transformometro_routes import router as transformometro_router
from tm_app.middleware.auth_middleware import jwt_middleware
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

    origins.add("http://localhost")
    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations_on_startup()
    yield


app = FastAPI(
    title="Transformômetro API",
    description="API do Transformômetro — melhorias de processo e ROI.",
    version="0.1.0",
    root_path=settings.TM_API_ROOT_PATH,
    lifespan=lifespan,
)

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
    return {"status": "online", "service": "transformometro-api"}


app.include_router(transformometro_router)
