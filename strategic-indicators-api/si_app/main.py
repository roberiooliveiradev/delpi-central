# strategic-indicators-api — entrypoint FastAPI (só rotas /strategic-indicators + health).
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from contextlib import asynccontextmanager

from delpi_auth.credential_guard import check_credentials

from si_app.application.services.strategic_indicators.period_scores_scheduler import (
    schedule_period_scores_refresh,
)
from si_app.application.services.strategic_indicators.snapshot_warmup_service import (
    schedule_strategic_indicators_warmup,
)
from si_app.startup.run_migrations_on_startup import run_migrations_on_startup
from si_app.config import settings
from si_app.interface.http.routes.integrations_routes import (
    router as strategic_indicators_integrations_router,
)
from si_app.interface.http.routes.strategic_indicators_routes import (
    router as strategic_indicators_router,
)
from si_app.middleware.auth_middleware import jwt_middleware

logging.basicConfig(
    level=getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def build_allowed_origins() -> list[str]:
    origins: set[str] = set()

    public_base_url = getattr(settings, "PUBLIC_BASE_URL", None)
    if public_base_url:
        origins.add(public_base_url.rstrip("/"))

    vite_kc_url = getattr(settings, "VITE_KC_URL", None)
    if vite_kc_url:
        if "/auth" in vite_kc_url:
            origins.add(vite_kc_url.split("/auth")[0].rstrip("/"))
        else:
            origins.add(vite_kc_url.rstrip("/"))

    # localhost only in development
    api_env = os.getenv("API_DELPI_ENV", "development")
    if api_env != "production":
        origins.add("http://localhost")

    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_credentials()
    run_migrations_on_startup()
    schedule_period_scores_refresh()
    if settings.SI_WARMUP_ON_STARTUP and not settings.SI_PERIOD_SCORES_REFRESH_ENABLED:
        schedule_strategic_indicators_warmup()
    yield


app = FastAPI(
    title="Strategic Indicators API",
    description="API de Indicadores Estratégicos (extraída da api-delpi).",
    version="1.0.0",
    root_path=settings.SI_API_ROOT_PATH,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["openapi"] = "3.0.3"

    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

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
    return {"status": "online"}

app.include_router(strategic_indicators_router)
app.include_router(strategic_indicators_integrations_router)


_SWAGGER_ENABLED = settings.API_ENV != "production"


@app.get("/docs", include_in_schema=False)
async def custom_swagger():
    if not _SWAGGER_ENABLED:
        return HTMLResponse(content="<h1>Docs desabilitado em produção</h1>", status_code=404)

    swagger_html = get_swagger_ui_html(
        openapi_url="openapi.json",
        title="Strategic Indicators API — Docs",
    )

    allowed_origins_js = "[" + ", ".join(f'"{origin}"' for origin in ALLOWED_ORIGINS) + "]"

    injected_script = f"""
    <script>
    window.DELPI_TOKEN = null;

    const ALLOWED_ORIGINS = {allowed_origins_js};

    function isOriginAllowed(origin) {{
        if (origin === window.location.origin) return true;
        return ALLOWED_ORIGINS.length > 0 && ALLOWED_ORIGINS.includes(origin);
    }}

    function applyToken(token) {{
        if (!window.ui || !token) return;

        try {{
            window.ui.preauthorizeApiKey("BearerAuth", token);
            console.log("Swagger autorizado automaticamente");
        }} catch (error) {{
            console.warn("Falha ao aplicar token no Swagger:", error);
        }}
    }}

    window.addEventListener("message", function (event) {{
        if (!isOriginAllowed(event.origin)) return;

        if (event.data?.type === "DELPI_AUTH" && event.data?.token) {{
            window.DELPI_TOKEN = event.data.token;
            applyToken(window.DELPI_TOKEN);
        }}
    }});

    const originalFetch = window.fetch.bind(window);

    window.fetch = async function () {{
        const response = await originalFetch.apply(this, arguments);

        if (response.status === 401) {{
            try {{
                if (window.parent && window.parent !== window) {{
                    const targetOrigin = ALLOWED_ORIGINS.includes(window.location.origin)
                        ? window.location.origin
                        : ALLOWED_ORIGINS[0];

                    if (targetOrigin) {{
                        window.parent.postMessage(
                            {{ type: "DELPI_REFRESH_REQUEST" }},
                            targetOrigin
                        );
                    }}
                }}
            }} catch (error) {{
                console.warn("Falha ao solicitar refresh do token:", error);
            }}
        }}

        return response;
    }};

    window.addEventListener("load", function () {{
        if (window.DELPI_TOKEN) {{
            applyToken(window.DELPI_TOKEN);
        }}
    }});
    </script>
    """

    html_content = swagger_html.body.decode("utf-8")
    html_content = html_content.replace("</body>", injected_script + "</body>")

    return HTMLResponse(content=html_content)


@app.get("/docs/", include_in_schema=False)
async def custom_swagger_slash():
    return await custom_swagger()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("si_app.main:app", host="0.0.0.0", port=8000, reload=True)
