from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from production_pulse_app.config import settings
from production_pulse_app.core.responses import error

PUBLIC_PATHS = frozenset({"/health"})


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path.rstrip("/") or "/"
        root = (settings.PRODUCTION_PULSE_API_ROOT_PATH or "").rstrip("/")
        if root and path.startswith(root):
            path = path[len(root) :] or "/"

        if path in PUBLIC_PATHS:
            return await call_next(request)

        if not settings.JWT_SECRET and not settings.KEYCLOAK_JWKS_URL:
            payload = error(
                "Autenticação não configurada.",
                code="auth_not_configured",
                status_code=503,
            )
            status_code = payload.pop("_status_code", 503)
            return JSONResponse(status_code=status_code, content=payload)

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            payload = error("Token ausente.", code="unauthorized", status_code=401)
            status_code = payload.pop("_status_code", 401)
            return JSONResponse(status_code=status_code, content=payload)

        return await call_next(request)
