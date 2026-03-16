# shared/delpi_auth/middleware/fastapi_auth.py
from types import SimpleNamespace

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

from ..jwt_validator import validate_token
from ..request_context import set_current_user


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
    path = request.url.path

    # --------------------------------
    # liberar docs e endpoints públicos
    # --------------------------------
    if is_public_path(path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"},
        )

    token = auth_header.split(" ", 1)[1]

    try:
        claims = validate_token(token)

        sub = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name") or email or "Usuário"

        if not sub or not email:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token claims"},
            )

        rbac = await load_user_rbac(token)

        user = SimpleNamespace(
            id=rbac.get("id"),
            email=rbac.get("email"),
            name=name,
            roles=rbac.get("roles", []),
            groups=rbac.get("groups", []),
            permissions=rbac.get("permissions", []),
            is_superadmin=rbac.get("is_superadmin", False),
        )

        request.state.user = user
        set_current_user(user)

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"},
        )

    return await call_next(request)