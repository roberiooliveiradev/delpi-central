"""MCP transport-facing OAuth + RFC 9728 protected-resource contract (S1).

Owns ONLY the transport/resource contract proven identical-or-configurable
across VISTA, TÉO and DAVI:

- ``WWW-Authenticate`` Bearer challenge construction (RFC 6750 + RFC 9728
  ``resource_metadata`` parameter);
- JWT ``scope``/``aud`` claim extraction and membership checks (pure claim
  processing — JWT validation itself stays in ``delpi_auth``);
- RFC 9728 protected-resource metadata document + route factory;
- the ``mcp/www_authenticate`` tool-result metadata envelope value;
- DNS-rebinding allowlist derivation shared by TÉO/DAVI.

Deliberately NOT owned here:

- JWT signature/claims validation (``delpi_auth``);
- business authorization (each domain application);
- per-app environment resolution (apps pass values/callables);
- issuer (RFC 8414) metadata or provider-specific extras.

Per-app wire differences preserved by parameters, not normalized away:

- VISTA joins challenge params with ``", "``, always emits the
  ``invalid_token`` pair and emits ``scope`` last; TÉO/DAVI join with
  ``" "`` and emit the full scope list before the optional error pair;
- VISTA emits ``resource_signing_alg_values_supported``; TÉO/DAVI do not;
- ``_meta["mcp/www_authenticate"]`` is a bare string on VISTA, a list on
  TÉO/DAVI (``wrap_in_list``);
- metadata alias paths differ per app (``metadata_paths``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Generic OAuth profile required on the MCP transport in all three apps.
# ``mcp:tools`` is a transport/resource-binding scope — never a business
# permission and never an ``audience-delpi``-style resource id.
MCP_TRANSPORT_SCOPES: tuple[str, ...] = ("openid", "profile", "email", "mcp:tools")

MCP_WWW_AUTHENTICATE_META_KEY = "mcp/www_authenticate"

# Browser/connector Origins used by ChatGPT MCP (DNS-rebinding allowlist
# only). Absent Origin remains allowed by TransportSecurityMiddleware.
MCP_CONNECTOR_ORIGINS: tuple[str, ...] = (
    "https://chatgpt.com",
    "https://chat.openai.com",
)


def _no_authorization_server() -> "str | None":
    return None


@dataclass(frozen=True)
class McpResourceConfig:
    """Per-MCP RFC 9728 resource configuration.

    Resolvers keep environment resolution app-local; every field has a real
    consumer in at least one of the three MCPs.
    """

    resolve_resource_url: Callable[[], str]
    resolve_authorization_server: Callable[[], "str | None"] = _no_authorization_server
    required_scopes: tuple[str, ...] = MCP_TRANSPORT_SCOPES
    resource_documentation: "str | None" = None
    resource_signing_alg_values_supported: "tuple[str, ...] | None" = None
    metadata_paths: tuple[str, ...] = ("/.well-known/oauth-protected-resource",)
    # Stable operation ids aligned with ``metadata_paths`` (DAVI/TÉO publish
    # them; operation-id audits treat auto-generated ids as drift).
    metadata_operation_ids: "tuple[str, ...] | None" = None


def extract_token_scopes(claims: Mapping[str, Any]) -> set[str]:
    raw = claims.get("scope") or claims.get("scp") or ""
    if isinstance(raw, (list, tuple, set)):
        return {str(item).strip() for item in raw if str(item).strip()}
    return {part for part in str(raw).split() if part}


def missing_required_scopes(
    claims: Mapping[str, Any], required: "tuple[str, ...] | list[str]"
) -> list[str]:
    present = extract_token_scopes(claims)
    return [scope for scope in required if scope not in present]


def extract_token_audiences(claims: Mapping[str, Any]) -> set[str]:
    raw = claims.get("aud")
    if raw is None:
        return set()
    if isinstance(raw, str):
        value = raw.strip()
        return {value} if value else set()
    if isinstance(raw, (list, tuple, set)):
        return {str(item).strip() for item in raw if str(item).strip()}
    return set()


def token_has_required_audience(claims: Mapping[str, Any], expected: str) -> bool:
    """Exact-membership resource binding. Fail-closed; extra audiences allowed.

    Proves token↔resource binding only — not business authorization.
    """
    target = (expected or "").strip()
    if not target:
        return False
    return target in extract_token_audiences(claims)


def protected_resource_metadata_url(resource_url: str) -> str:
    """Metadata URL: strip a trailing ``/mcp`` mount, append the well-known."""
    parsed = urlparse(resource_url.rstrip("/"))
    path = parsed.path
    if path.endswith("/mcp"):
        path = path[: -len("/mcp")]
    return f"{parsed.scheme}://{parsed.netloc}{path}/.well-known/oauth-protected-resource"


def build_www_authenticate_challenge(
    *,
    realm: str,
    metadata_url: str,
    scope_value: "str | None",
    separator: str = " ",
    scope_last: bool = False,
    default_error: "tuple[str, str] | None" = None,
    error: "str | None" = None,
    error_description: "str | None" = None,
) -> str:
    """RFC 6750 Bearer challenge carrying the RFC 9728 ``resource_metadata`` hint.

    ``scope_value``: a string is emitted verbatim; empty/None omits the
    ``scope`` parameter entirely. ``error_description`` has embedded double
    quotes replaced by single quotes (existing TÉO/DAVI sanitization).
    """
    parts = [
        f'Bearer realm="{realm}"',
        f'resource_metadata="{metadata_url}"',
    ]
    if not scope_last and scope_value:
        parts.append(f'scope="{scope_value}"')
    if not error and default_error is not None:
        error, error_description = default_error
    if error:
        parts.append(f'error="{error}"')
    if error_description:
        safe = error_description.replace('"', "'")
        parts.append(f'error_description="{safe}"')
    if scope_last and scope_value:
        parts.append(f'scope="{scope_value}"')
    return separator.join(parts)


def build_www_authenticate_meta(challenge: str, *, wrap_in_list: bool) -> dict[str, Any]:
    """``_meta["mcp/www_authenticate"]`` envelope — list or bare string per app."""
    return {MCP_WWW_AUTHENTICATE_META_KEY: [challenge] if wrap_in_list else challenge}


def build_protected_resource_metadata(
    config: McpResourceConfig, *, resource_url: "str | None" = None
) -> dict[str, Any]:
    """RFC 9728 protected-resource metadata document."""
    resource = (resource_url or config.resolve_resource_url()).rstrip("/")
    issuer = config.resolve_authorization_server()
    doc: dict[str, Any] = {
        "resource": resource,
        "authorization_servers": [issuer] if issuer else [],
        "scopes_supported": list(config.required_scopes),
        "bearer_methods_supported": ["header"],
    }
    if config.resource_signing_alg_values_supported:
        doc["resource_signing_alg_values_supported"] = list(
            config.resource_signing_alg_values_supported
        )
    if config.resource_documentation:
        doc["resource_documentation"] = config.resource_documentation
    return doc


def mcp_metadata_router(config: McpResourceConfig, *, tags: "list[str] | None" = None):
    """APIRouter serving the RFC 9728 document on every configured alias path.

    Fail-safe shape ``{"error": "metadata_unavailable"}`` + 503 matches the
    existing VISTA contract; the builder is pure so it never fires for
    static configurations.
    """
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter(tags=list(tags or ()))
    operation_ids = config.metadata_operation_ids or (None,) * len(config.metadata_paths)
    for path, operation_id in zip(config.metadata_paths, operation_ids):

        async def _protected_resource_metadata() -> JSONResponse:
            try:
                return JSONResponse(build_protected_resource_metadata(config))
            except Exception as exc:
                logger.warning(
                    "oauth-protected-resource metadata failed: %s", type(exc).__name__
                )
                return JSONResponse({"error": "metadata_unavailable"}, status_code=503)

        router.get(path, include_in_schema=False, operation_id=operation_id)(
            _protected_resource_metadata
        )
    return router


def mcp_allowed_hosts_and_origins(
    public_base_url: "str | None",
) -> "tuple[list[str], list[str]]":
    """Hosts/origins for MCP DNS-rebinding protection from the public base URL."""
    hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    origins = [
        "http://127.0.0.1:*",
        "http://localhost:*",
        "http://[::1]:*",
        *MCP_CONNECTOR_ORIGINS,
    ]
    if not public_base_url:
        return hosts, origins
    parsed = urlparse(public_base_url)
    host = parsed.hostname
    if not host:
        return hosts, origins
    hosts.append(host)
    hosts.append(f"{host}:*")
    scheme = parsed.scheme or "https"
    if parsed.port:
        origins.append(f"{scheme}://{host}:{parsed.port}")
    else:
        origins.append(f"{scheme}://{host}")
    return hosts, origins


__all__ = [
    "MCP_CONNECTOR_ORIGINS",
    "MCP_TRANSPORT_SCOPES",
    "MCP_WWW_AUTHENTICATE_META_KEY",
    "McpResourceConfig",
    "build_protected_resource_metadata",
    "build_www_authenticate_challenge",
    "build_www_authenticate_meta",
    "extract_token_audiences",
    "extract_token_scopes",
    "mcp_allowed_hosts_and_origins",
    "mcp_metadata_router",
    "missing_required_scopes",
    "protected_resource_metadata_url",
    "token_has_required_audience",
]
