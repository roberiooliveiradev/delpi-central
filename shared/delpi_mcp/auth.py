"""Shared MCP transport authentication middleware (S3).

Owns ONLY the transport-binding gate duplicated across VISTA/TÉO/DAVI:

- internal service tokens forbidden on the MCP user-data surface;
- Bearer extraction (missing/malformed/empty → fail closed);
- JWT validation via ``delpi_auth.validate_token`` (canonical owner);
- exact resource audience membership (S1 ``token_has_required_audience``);
- required scope presence (S1 ``missing_required_scopes``);
- delegation to the existing ``delpi_auth`` FastAPI middleware, which remains
  the owner of ``request.state.user``, ContextVars and RBAC loading;
- optional re-decoration of a base-middleware 401 with the MCP challenge.

Audience/scopes are a *transport binding* — never business permission.
This module contains no domain knowledge, no role/permission checks and no
identity-bridge semantics (S4/S5 remain separate phases).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Mapping

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from delpi_auth.jwt_validator import validate_token as _validate_token
from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as _base_jwt_middleware,
)
from delpi_auth.service_token import request_has_valid_internal_service_token

from .resource_contract import missing_required_scopes, token_has_required_audience

logger = logging.getLogger("delpi_mcp.auth")

__all__ = [
    "McpTransportAuthPolicy",
    "is_mcp_data_path",
    "mcp_transport_auth",
]

# Safe failure vocabulary for logs — transport diagnostics only. The wire
# challenge stays generic; internals are never exposed to the client.
_CLASS_SERVICE_TOKEN = "SERVICE_TOKEN_FORBIDDEN"
_CLASS_MISSING_BEARER = "MISSING_BEARER"
_CLASS_EMPTY_BEARER = "INVALID_BEARER"
_CLASS_VALIDATION_FAILED = "TOKEN_VALIDATION_FAILED"
_CLASS_AUDIENCE_MISMATCH = "RESOURCE_AUDIENCE_MISMATCH"
_CLASS_MISSING_SCOPE = "MISSING_REQUIRED_SCOPE"


def is_mcp_data_path(normalized_path: str) -> bool:
    """True for the MCP JSON-RPC transport mount (``/mcp`` and subpaths).

    The caller passes an already-normalized path — each app keeps its own
    root_path/prefix normalization (legitimate variation).
    """
    return normalized_path == "/mcp" or normalized_path.startswith("/mcp/")


@dataclass(frozen=True)
class McpTransportAuthPolicy:
    """Per-app wire/config knobs for the shared MCP transport AuthN.

    ``resolve_resource_audience``: resolves the exact resource URL required in
    JWT ``aud`` (env/canonical per app). Evaluated per request; an empty or
    unresolvable value fails closed — protected MCP never becomes permissive.

    ``required_scopes``: scopes required in the JWT ``scope`` claim
    (transport binding only, e.g. ``("openid", "profile", "email",
    "mcp:tools")``).

    ``challenge``: builds the ``WWW-Authenticate`` value for a transport 401.
    Called as ``challenge(error=..., error_description=...)``; apps whose wire
    format is generic may ignore both parameters (e.g. VISTA comma-style
    challenge).

    ``redecorate_base_401``: when True, a 401 produced by the delegated
    ``delpi_auth`` base middleware has its ``WWW-Authenticate`` overwritten
    with the MCP challenge (DAVI/TÉO current behavior). VISTA passes False —
    its base 401 keeps the base-middleware header unchanged.
    """

    resolve_resource_audience: Callable[[], str]
    required_scopes: tuple[str, ...]
    challenge: Callable[..., str]
    redecorate_base_401: bool = True


def _json_401(challenge_value: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={"WWW-Authenticate": challenge_value},
    )


async def mcp_transport_auth(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    *,
    policy: McpTransportAuthPolicy,
    token_validator: Callable[[str], Mapping[str, Any]] = _validate_token,
    service_token_gate: Callable[[Request], bool] = request_has_valid_internal_service_token,
    base_auth_middleware: Callable[
        [Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]
    ] = _base_jwt_middleware,
) -> Response:
    """MCP transport AuthN gate, then delegate to the canonical base middleware.

    Fail-closed at every step. No identity is placed on ``request.state`` or
    ContextVars here — only ``base_auth_middleware`` (delpi_auth) establishes
    canonical user context after full transport validation.
    """
    path = request.url.path

    # User-data surface: machine/service identity is forbidden.
    if service_token_gate(request):
        logger.warning("mcp_auth_denied class=%s path=%s", _CLASS_SERVICE_TOKEN, path)
        return _json_401(
            policy.challenge(
                error="invalid_token",
                error_description="User authentication required",
            )
        )

    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        logger.warning("mcp_auth_denied class=%s path=%s", _CLASS_MISSING_BEARER, path)
        return _json_401(
            policy.challenge(
                error="invalid_token",
                error_description="Authentication required",
            )
        )

    token = auth.split(" ", 1)[1].strip()
    if not token:
        logger.warning("mcp_auth_denied class=%s path=%s", _CLASS_EMPTY_BEARER, path)
        return _json_401(
            policy.challenge(
                error="invalid_token",
                error_description="Authentication required",
            )
        )

    try:
        # 1) Canonical platform JWT validation (signature/issuer/exp/nbf/aud).
        claims = token_validator(token)
        # 2) Exact MCP resource audience membership — transport binding only.
        resource = (policy.resolve_resource_audience() or "").strip()
        if not resource or not token_has_required_audience(claims, resource):
            logger.warning(
                "mcp_auth_denied class=%s path=%s", _CLASS_AUDIENCE_MISMATCH, path
            )
            return _json_401(
                policy.challenge(
                    error="invalid_token",
                    error_description="MCP resource audience is required",
                )
            )
        # 3) Required OAuth scopes in the JWT scope claim.
        missing = missing_required_scopes(claims, policy.required_scopes)
        if missing:
            logger.warning(
                "mcp_auth_denied class=%s path=%s missing=%s",
                _CLASS_MISSING_SCOPE,
                path,
                ",".join(missing),
            )
            return _json_401(
                policy.challenge(
                    error="insufficient_scope",
                    error_description="Required OAuth scopes are missing",
                )
            )
    except Exception:
        logger.warning(
            "mcp_auth_denied class=%s path=%s", _CLASS_VALIDATION_FAILED, path
        )
        return _json_401(
            policy.challenge(
                error="invalid_token",
                error_description="Access token validation failed",
            )
        )

    response = await base_auth_middleware(request, call_next)
    if policy.redecorate_base_401 and getattr(response, "status_code", None) == 401:
        response.headers["WWW-Authenticate"] = policy.challenge(
            error="invalid_token",
            error_description="Authentication required",
        )
    return response
