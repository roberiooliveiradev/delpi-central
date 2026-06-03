# shared/delpi_auth/middleware/fastapi_auth.py
import asyncio
import hashlib
import logging
import os
import time
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

logger = logging.getLogger(__name__)

CORE_API_URL = os.getenv("DELPI_AUTH_CORE_API_URL") or os.getenv("CORE_API_URL") or "http://core-api:8000"
RBAC_TIMEOUT_SECONDS = float(os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS", "2.5"))
RBAC_CACHE_TTL_SECONDS = int(os.getenv("DELPI_AUTH_RBAC_CACHE_TTL_SECONDS", "60"))
RBAC_STALE_TTL_SECONDS = int(os.getenv("DELPI_AUTH_RBAC_STALE_TTL_SECONDS", "900"))

_RBAC_CACHE: dict[str, tuple[float, float, dict]] = {}
_RBAC_LOCKS: dict[str, asyncio.Lock] = {}

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


def _cache_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _rbac_from_claims(claims: dict, token: str, *, rbac_unavailable: bool = False) -> dict:
    email = claims.get("email")
    name = claims.get("name") or email or "Usuário"
    roles = claims.get("roles") or claims.get("realm_access", {}).get("roles", []) or []
    groups = claims.get("groups") or []

    return {
        "id": claims.get("sub"),
        "email": email,
        "name": name,
        "roles": roles,
        "groups": groups,
        "permissions": [],
        "is_superadmin": False,
        "rbac_unavailable": rbac_unavailable,
        "access_token": token,
    }


async def load_user_rbac(token: str):
    key = _cache_key(token)
    now = time.monotonic()

    cached = _RBAC_CACHE.get(key)
    if cached:
        expires_at, _stale_until, data = cached
        if now <= expires_at:
            return data

    lock = _RBAC_LOCKS.setdefault(key, asyncio.Lock())
    async with lock:
        now = time.monotonic()
        cached = _RBAC_CACHE.get(key)
        if cached:
            expires_at, _stale_until, data = cached
            if now <= expires_at:
                return data

        try:
            timeout = httpx.Timeout(RBAC_TIMEOUT_SECONDS, connect=RBAC_TIMEOUT_SECONDS)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(
                    f"{CORE_API_URL}/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

            if resp.status_code != 200:
                raise RuntimeError(f"RBAC lookup failed with status {resp.status_code}")

            data = resp.json()
            _RBAC_CACHE[key] = (
                now + RBAC_CACHE_TTL_SECONDS,
                now + RBAC_STALE_TTL_SECONDS,
                data,
            )
            return data

        except (httpx.TimeoutException, httpx.RequestError, RuntimeError):
            cached = _RBAC_CACHE.get(key)
            if cached:
                _expires_at, stale_until, data = cached
                if now <= stale_until:
                    logger.warning(
                        "rbac_lookup_failed_using_stale_cache core_api_url=%s",
                        CORE_API_URL,
                        exc_info=True,
                    )
                    return data
            raise
        finally:
            # Evita crescimento indefinido da tabela de locks em processos longos.
            if key in _RBAC_LOCKS and not _RBAC_LOCKS[key].locked():
                _RBAC_LOCKS.pop(key, None)


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
            logger.exception("unhandled_error_service_request path=%s", path)
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
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

        try:
            rbac = await load_user_rbac(token)
        except Exception:
            logger.warning(
                "rbac_lookup_unavailable_using_token_claims path=%s core_api_url=%s",
                path,
                CORE_API_URL,
                exc_info=True,
            )
            rbac = _rbac_from_claims(claims, token, rbac_unavailable=True)

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
        logger.exception("token_validation_failed path=%s", path)
        reset_request_authorization(auth_context_token)
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    try:
        return await call_next(request)
    except Exception as e:
        logger.exception("unhandled_error_authenticated_request path=%s", path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        reset_request_authorization(auth_context_token)
        if context_token is not None:
            reset_current_user(context_token)
        else:
            clear_current_user()
