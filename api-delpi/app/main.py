# app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

from app.startup.run_plugins_migrations_on_startup import (
    run_plugins_migrations_on_startup,
)

from app.interface.socket.audit_5s_handlers import register_audit_5s_socket_handlers
from app.interface.socket.sio_server import create_socket_app
from delpi_auth.credential_guard import check_credentials
from app.config import settings
from app.interface.http.routes import customer_routes, product_drawing_routes, product_routes
from app.interface.http.routes import system_routes
from app.interface.http.routes import data_routes
from app.interface.http.routes import sale_routes
from app.interface.http.routes.financial import financial_routes
from app.interface.http.routes.supplies import supplies_router
from app.interface.http.routes.commercial import commercial_router
from app.interface.http.routes.production import production_router
from app.interface.http.routes.production import production_operational_router
from app.interface.http.routes.purchases import purchases_router
from app.interface.http.routes.engineering import engineering_router
from app.interface.http.routes.quality import quality_router
from app.interface.http.routes.hr import hr_router
from app.interface.http.routes.dashboard import dashboard_router
from app.interface.http.routes.scheduling import scheduling_router
from app.interface.http.routes.cultura_delpi import cultura_delpi_router
from app.interface.http.routes.inspecoes_entrada import inspecoes_entrada_router
from app.interface.http.routes.pedidos_venda_abertos import pedidos_venda_abertos_router
from app.interface.http import propostas_comerciais_controller
from app.core.responses import error_response, not_found_response
from app.middleware.auth_middleware import jwt_middleware
from app.middleware.pac_service_actor_middleware import pac_service_actor_middleware
from app.middleware.app_usage_tracking_middleware import app_usage_tracking_middleware
from app.middleware.request_observability_middleware import request_observability_middleware
from app.interface.http.swagger_portal_bridge import build_swagger_portal_bridge_script


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

    # localhost only in development
    api_env = os.getenv("API_DELPI_ENV", "development")
    if api_env != "production":
        origins.add("http://localhost")

    return sorted(origins)


ALLOWED_ORIGINS = build_allowed_origins()

check_credentials()

# ==========================================================
# FASTAPI CONFIG
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_plugins_migrations_on_startup()
    yield


app = FastAPI(
    title="API DELPI",
    description="API RESTful para integração com o TOTVS Protheus.",
    version="1.0.0",
    root_path="/apps/api-delpi",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
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

    from app.interface.http.openapi_delpi_extension_injector import inject_delpi_extensions

    inject_delpi_extensions(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ==========================================================
# EXCEPTION HANDLERS (envelope unificado)
# ==========================================================


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    if exc.status_code == 404:
        return not_found_response(detail or "Recurso não encontrado")
    code = "VALIDATION_ERROR" if exc.status_code == 422 else "HTTP_ERROR"
    return error_response(detail, status_code=exc.status_code, code=code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return error_response(
        "Parâmetros inválidos",
        status_code=422,
        code="VALIDATION_ERROR",
        recoverable=True,
    )


# ==========================================================
# MIDDLEWARE
# ==========================================================

app.middleware("http")(jwt_middleware)
app.middleware("http")(pac_service_actor_middleware)
app.middleware("http")(request_observability_middleware)
app.middleware("http")(app_usage_tracking_middleware)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Operation-Id", "X-Response-Time-Ms"],
)


# ==========================================================
# ROUTES
# ==========================================================

@app.get("/health", tags=["Health"])
def root():
    return {"status": "online"}

app.include_router(
    financial_routes.router,
    prefix="/finacial",
    tags=["Financeiro"],
    include_in_schema=False,
)
app.include_router(financial_routes.router, prefix="/financial", tags=["Financeiro"])
app.include_router(supplies_router.router)  
app.include_router(commercial_router.router)
app.include_router(production_router.router)
app.include_router(production_operational_router.router)
app.include_router(purchases_router.router)
app.include_router(engineering_router.router)
app.include_router(quality_router.router)
app.include_router(hr_router.router)
app.include_router(dashboard_router.router)
app.include_router(scheduling_router.router, prefix="/scheduling", tags=["Agendamento"])
app.include_router(
    cultura_delpi_router.router,
    prefix="/cultura-delpi",
    tags=["Cultura DELPI"],
)
app.include_router(product_drawing_routes.router, prefix="/products", tags=["products"])
app.include_router(product_routes.router, prefix="/products", tags=["products"])
app.include_router(customer_routes.router)
app.include_router(sale_routes.router, prefix="/sales", tags=["sales"])
app.include_router(system_routes.router, prefix="/system", tags=["system"])
app.include_router(data_routes.router, prefix="/data", tags=["data"])
app.include_router(inspecoes_entrada_router.router)
app.include_router(pedidos_venda_abertos_router.router)
app.include_router(propostas_comerciais_controller.router)

register_audit_5s_socket_handlers()

# ASGI app exposto ao uvicorn (FastAPI + Socket.IO)
socket_app = create_socket_app(app)


# ==========================================================
# CUSTOM SWAGGER (COM POSTMESSAGE + REFRESH)
# ==========================================================

@app.get("/docs", include_in_schema=False)
async def custom_swagger():
    swagger_html = get_swagger_ui_html(
        openapi_url="openapi.json",
        title="API DELPI Docs",
    )

    injected_bridge = build_swagger_portal_bridge_script(ALLOWED_ORIGINS)

    html_content = swagger_html.body.decode("utf-8")
    html_content = html_content.replace("</body>", injected_bridge + "</body>")

    return HTMLResponse(content=html_content)


@app.get("/docs/", include_in_schema=False)
async def custom_swagger_slash():
    return await custom_swagger()


# ==========================================================
# DEV RUN
# ==========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.asgi:application", host="0.0.0.0", port=8000, reload=True)