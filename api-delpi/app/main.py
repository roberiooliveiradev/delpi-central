# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import Request

from app.config import settings
from app.interface.http.routes import product_routes
from app.interface.http.routes import system_routes
from app.interface.http.routes import data_routes
from app.middleware.auth_middleware import jwt_middleware

# ==========================================================
# FASTAPI CONFIG 
# ==========================================================

app = FastAPI(
    title="API DELPI",
    description="API RESTful para integração com o TOTVS Protheus.",
    version="1.0.0",
    root_path="/apps/api-delpi",  # 🔥 ESSENCIAL COM NGINX
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

    # GARANTE versão válida
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
    allow_origins=["*"],  # Ajustar em produção
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

    injected_script = """
    <script>
    window.DELPI_TOKEN = null;

    function applyToken(token) {
        if (!window.ui) return;
        window.ui.preauthorizeApiKey("BearerAuth", token);
    }

    window.addEventListener("message", function (event) {
        if (!event.origin.startsWith("http://localhost")) return;

        if (event.data?.type === "DELPI_AUTH") {
            window.DELPI_TOKEN = event.data.token;
            applyToken(window.DELPI_TOKEN);
            console.log("Swagger autorizado automaticamente 🔐");
        }
    });

    const originalFetch = window.fetch;
    window.fetch = async function() {
        const response = await originalFetch.apply(this, arguments);

        if (response.status === 401) {
            window.parent.postMessage(
                { type: "DELPI_REFRESH_REQUEST" },
                "http://localhost"
            );
        }

        return response;
    };
    </script>
    """

    html_content = swagger_html.body.decode("utf-8")
    html_content = html_content.replace("</body>", injected_script + "</body>")

    return HTMLResponse(content=html_content)

# ==========================================================
# DEV RUN
# ==========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)