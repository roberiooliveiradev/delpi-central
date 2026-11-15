"""Isolated ASGI MCP adapter; deliberately no runtime/host access."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as canonical_jwt_middleware, normalize_path,
)
from delpi_auth.service_token import request_has_valid_internal_service_token
from delpi_mcp.auth import (
    McpTransportAuthPolicy, is_mcp_data_path, mcp_transport_auth,
)
from delpi_mcp.resource_contract import (
    McpResourceConfig, MCP_TRANSPORT_SCOPES,
    build_www_authenticate_challenge, mcp_metadata_router,
)
from delpi_mcp.transport import combine_lifespans, mcp_mount_path_middleware

from .server import create_mcp_server, security_settings

APP_PATH = "/apps/linux-ops-mcp"
DEFAULT_RESOURCE = "https://minhadelpi.com.br/apps/linux-ops-mcp/mcp"


def resource_url() -> str:
    resource = (os.getenv("LINUX_OPS_MCP_RESOURCE_URL") or "").strip().rstrip("/")
    if not resource:
        # No implicit production deployment URL when auth config is missing.
        raise ValueError("LINUX_OPS_MCP_RESOURCE_URL missing")
    if not resource.startswith("https://") or not resource.endswith("/mcp"):
        raise ValueError("invalid resource URL")
    return resource


def issuer_url() -> str:
    issuer = (os.getenv("KEYCLOAK_ISSUER") or "").strip()
    if not issuer.startswith("https://"):
        raise ValueError("KEYCLOAK_ISSUER missing")
    return issuer


resource_config = McpResourceConfig(
    resolve_resource_url=resource_url,
    resolve_authorization_server=issuer_url,
    required_scopes=MCP_TRANSPORT_SCOPES,
)


def challenge(*, error: str | None = None, error_description: str | None = None) -> str:
    # Do not insert untrusted values into the challenge header.
    try:
        metadata_url = resource_url().removesuffix("/mcp") + "/.well-known/oauth-protected-resource"
    except ValueError:
        metadata_url = DEFAULT_RESOURCE.removesuffix("/mcp") + "/.well-known/oauth-protected-resource"
    return build_www_authenticate_challenge(
        realm="delpi-linux-ops",
        metadata_url=metadata_url,
        scope_value=" ".join(MCP_TRANSPORT_SCOPES),
        error=error,
        error_description=error_description,
    )


auth_policy = McpTransportAuthPolicy(
    resolve_resource_audience=resource_url,
    required_scopes=MCP_TRANSPORT_SCOPES,
    challenge=challenge,
    redecorate_base_401=True,
)


async def auth_middleware(request, call_next):
    path = normalize_path(request.url.path)
    if path in {"/healthz", "/.well-known/oauth-protected-resource"}:
        return await call_next(request)
    if is_mcp_data_path(path):
        return await mcp_transport_auth(
            request,
            call_next,
            policy=auth_policy,
            token_validator=validate_token,
            service_token_gate=request_has_valid_internal_service_token,
            base_auth_middleware=canonical_jwt_middleware,
        )
    return JSONResponse({"detail": "Not found"}, status_code=404)


mcp = create_mcp_server()
transport = mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=security_settings(),
)


@asynccontextmanager
async def _lifespan(_app: Any):
    # Fail closed before accepting traffic if any identity configuration is absent.
    resource_url()
    issuer_url()
    from .reader import Settings
    Settings.from_environment()
    yield


def create_app():
    app = FastAPI(
        title="Delpi Linux Operations MCP (read-only)",
        version="0.1.0",
        redirect_slashes=False,
        lifespan=combine_lifespans(
            _lifespan,
            lambda _app: transport.router.lifespan_context(transport),
        ),
    )
    app.middleware("http")(auth_middleware)
    app.middleware("http")(mcp_mount_path_middleware(frozenset({"/mcp"})))
    app.include_router(mcp_metadata_router(resource_config))
    @app.get("/healthz", include_in_schema=False)
    async def healthz():
        return {"status": "ok", "mode": "read_only"}
    app.mount("/mcp", transport)
    return app


app = create_app()
