# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

from app.config import settings
from app.interface.http.routes import product_routes
from app.interface.http.routes import system_routes
from app.interface.http.routes import data_routes
from app.interface.http.routes import sale_routes
from app.interface.http.routes import lmp_routes
from app.middleware.auth_middleware import jwt_middleware


# ==========================================================
# HELPERS
# ==========================================================

def build_allowed_origins() -> list[str]:
    origins = set()

    public_base_url = getattr(settings, "PUBLIC_BASE_URL", None)
    if public_base_url:
        origins.add(public_base_url.rstrip("/"))

    vite_kc_url = getattr(settings, "VITE_KC_URL", None)
    if vite_kc_url:
        if "/auth" in vite_kc_url:
            origins.add(vite_kc_url.split("/auth")[0].rstrip("/"))
        else:
            origins.add(vite_kc_url.rstrip("/"))

    # fallback útil para desenvolvimento
    origins.add("http://localhost")

    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()


# ==========================================================
# FASTAPI CONFIG
# ==========================================================

app = FastAPI(
    title="API DELPI",
    description="API RESTful para integração com o TOTVS Protheus.",
    version="1.0.0",
    root_path="/apps/api-delpi",
    docs_url=None,
    redoc_url=None,
)


# ==========================================================
# OPENAPI CONFIG
# ==========================================================

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


# ==========================================================
# MIDDLEWARE
# ==========================================================

app.middleware("http")(jwt_middleware)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# ROUTES
# ==========================================================

@app.get("/health", tags=["Health"])
def root():
    return {"status": "online"}


app.include_router(product_routes.router, prefix="/products", tags=["products"])
app.include_router(sale_routes.router, prefix="/sales", tags=["sales"])
app.include_router(lmp_routes.router, prefix="/lmps", tags=["lmps"])
app.include_router(system_routes.router, prefix="/system", tags=["system"])
app.include_router(data_routes.router, prefix="/data", tags=["data"])


# ==========================================================
# CUSTOM SWAGGER (COM POSTMESSAGE + REFRESH)
# ==========================================================

@app.get("/docs", include_in_schema=False)
async def custom_swagger():
    swagger_html = get_swagger_ui_html(
        openapi_url="openapi.json",
        title="API DELPI Docs",
    )

    allowed_origins_js = "[" + ", ".join(f'"{origin}"' for origin in ALLOWED_ORIGINS) + "]"

    injected_script = f"""
    <script>
    window.DELPI_TOKEN = null;

    const ALLOWED_ORIGINS = {allowed_origins_js};

    function applyToken(token) {{
        if (!window.ui || !token) return;

        try {{
            window.ui.preauthorizeApiKey("BearerAuth", token);
            console.log("Swagger autorizado automaticamente 🔐");
        }} catch (error) {{
            console.warn("Falha ao aplicar token no Swagger:", error);
        }}
    }}

    window.addEventListener("message", function (event) {{
        if (!ALLOWED_ORIGINS.includes(event.origin)) return;

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


# ==========================================================
# DEV RUN
# ==========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)