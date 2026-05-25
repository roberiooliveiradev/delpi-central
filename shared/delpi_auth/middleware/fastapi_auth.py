# shared/delpi_auth/middleware/fastapi_auth.py
from types import SimpleNamespace

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

from ..jwt_validator import validate_token
from ..request_context import (
    set_current_user,
    reset_current_user,
    clear_current_user,
    set_request_authorization,
    reset_request_authorization,
    clear_request_authorization,
)
from ..service_token import request_has_valid_internal_service_token


CORE_API_URL = "http://core-api:8000"

PUBLIC_SUFFIXES = (
    "/docs",
    "/docs/",
    "/redoc",
    "/redoc/",
    "/openapi.json",
    "/health",
)


def normalize_path(path: str) -> str:
    if not path:
        return "/"

    normalized = path.split("?", 1)[0]

    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")

    return normalized


def is_public_path(path: str) -> bool:
    raw_path = path.split("?", 1)[0]
    normalized = normalize_path(path)

    public_base_paths = {"/docs", "/redoc", "/openapi.json", "/health"}

    return (
        raw_path.endswith(PUBLIC_SUFFIXES)
        or normalized in public_base_paths
        or any(normalized.endswith(public_path) for public_path in public_base_paths)
    )


async def load_user_rbac(token: str):
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(
            f"{CORE_API_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        raise Exception("RBAC lookup failed")

    return resp.json()


async def jwt_middleware(request: Request, call_next):
    clear_current_user()
    clear_request_authorization()

    path = request.url.path
    if is_public_path(path):
        return await call_next(request)

    if request_has_valid_internal_service_token(request):
        service_user = SimpleNamespace(
            id="internal-service",
            email="service@delpi.internal",
            name="Serviço Interno",
            roles=["internal-service"],
            groups=[],
            permissions=[],
            is_superadmin=True,
            access_token=None,
        )
        request.state.user = service_user
        context_token = set_current_user(service_user)
        auth_context_token = set_request_authorization(
            request.headers.get("Authorization") or ""
        )
        try:
            return await call_next(request)
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Error: {e}"})
        finally:
            reset_request_authorization(auth_context_token)
            reset_current_user(context_token)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header.split(" ", 1)[1]
    context_token = None
    auth_context_token = set_request_authorization(auth_header)

    try:
        claims = validate_token(token)
        sub = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name") or email or "Usuário"

        if not sub or not email:
            reset_request_authorization(auth_context_token)
            return JSONResponse(status_code=401, content={"detail": "Invalid token claims"})

        rbac = await load_user_rbac(token)

        user = SimpleNamespace(
            id=rbac.get("id") or sub,
            email=rbac.get("email") or email,
            name=rbac.get("name") or name,
            roles=rbac.get("roles", []),
            groups=rbac.get("groups", []),
            permissions=rbac.get("permissions", []),
            is_superadmin=rbac.get("is_superadmin", False),
            access_token=token,
        )

        request.state.user = user
        context_token = set_current_user(user)

    except Exception as exc:
        reset_request_authorization(auth_context_token)
        return JSONResponse(status_code=401, content={"detail": f"Invalid token: {exc}"})

    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail":f"Error: {e}"})
    finally:
        reset_request_authorization(auth_context_token)
        if context_token is not None:
            reset_current_user(context_token)
        else:
            clear_current_user()