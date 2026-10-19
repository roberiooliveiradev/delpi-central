# shared/delpi_auth/cors_policy.py
"""Canonical CORS origin policy for Minha DELPI HTTP services.

Platform rule (platform-security-identity-authorization.mdc): CORS is
restrictive — only explicitly authorized origins receive CORS headers.
This module is the single source that builds the allowlist:

- ``PUBLIC_BASE_URL`` (portal/gateway public origin)
- ``VITE_KC_URL`` (Keycloak origin, ``/auth`` suffix stripped)
- ``http://localhost`` only when the resolved environment is an
  explicitly authorized local-class value (``API_DELPI_ENV``);
  absent or unknown values never enable localhost.
- app-owned extras (e.g. Custom GPT origins) passed explicitly.

Every input is normalized strictly to ``scheme://host[:port]``; values
carrying paths, queries, fragments, credentials or malformed authority
are rejected rather than repaired. Never produces a wildcard. When the
resulting list is empty, callers must pass it through unchanged —
Starlette/python-socketio then deny every cross-origin browser request
while same-origin and server-to-server traffic keep working.
"""

import logging
import os
from collections.abc import Iterable, Mapping
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

LOCALHOST_ORIGIN = "http://localhost"
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_LOCALHOST_ALLOWED_ENVS = frozenset({"development", "dev", "local", "test"})


def normalize_origin(value: "str | None") -> "str | None":
    """Return a normalized ``scheme://host[:port]`` origin or ``None``.

    Strictly validates the input as an origin: absolute ``http``/``https``
    URL with a host, optional numeric port and nothing else. Paths (other
    than a bare ``/``), queries, fragments, embedded credentials,
    wildcards and malformed authorities are rejected — never repaired —
    so a bad value can never widen access.
    """
    if not value:
        return None
    candidate = str(value).strip()
    if not candidate or candidate == "*":
        return None
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        return None
    if any(char.isspace() for char in parts.netloc):
        return None
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        return None
    if not host or "*" in host:
        return None
    host = host.lower()
    if ":" in host:
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port is not None else host
    return f"{scheme}://{netloc}"


def _keycloak_origin(keycloak_url: "str | None") -> "str | None":
    if not keycloak_url:
        return None
    raw = str(keycloak_url).strip()
    if "/auth" in raw:
        raw = raw.split("/auth")[0]
    return raw


def build_allowed_origins(
    *,
    public_base_url: "str | None" = None,
    keycloak_url: "str | None" = None,
    extra_origins: Iterable[str] = (),
    environment: "str | None" = None,
    environ: "Mapping[str, str] | None" = None,
) -> "list[str]":
    """Build the validated CORS allowlist for a service.

    Args:
        public_base_url: portal public origin; falls back to the
            ``PUBLIC_BASE_URL`` env var when not provided.
        keycloak_url: Keycloak base URL; falls back to ``VITE_KC_URL``.
        extra_origins: app-owned additional origins (never ``*``).
        environment: explicit environment name; falls back to
            ``API_DELPI_ENV``. Only values in
            ``_LOCALHOST_ALLOWED_ENVS`` authorize the localhost origin;
            absent or unknown values are treated as non-local.
        environ: env mapping override for tests.

    Returns:
        Sorted unique list of authorized origins. May be empty — callers
        must not substitute ``["*"]``.
    """
    env_map: Mapping[str, str] = os.environ if environ is None else environ

    if public_base_url is None:
        public_base_url = env_map.get("PUBLIC_BASE_URL")
    if keycloak_url is None:
        keycloak_url = env_map.get("VITE_KC_URL")

    resolved_env = (
        environment
        if environment is not None
        else env_map.get("API_DELPI_ENV")
    )
    env_name = str(resolved_env).strip().lower() if resolved_env else ""
    localhost_allowed = env_name in _LOCALHOST_ALLOWED_ENVS

    origins: set[str] = set()
    for raw in (public_base_url, _keycloak_origin(keycloak_url)):
        normalized = normalize_origin(raw)
        if normalized:
            origins.add(normalized)
        elif raw and str(raw).strip():
            logger.warning(
                "CORS origin rejected as invalid (value hidden): "
                "only absolute http(s) origins are allowed"
            )

    if localhost_allowed:
        origins.add(LOCALHOST_ORIGIN)

    for raw in extra_origins:
        normalized = normalize_origin(raw)
        if normalized:
            origins.add(normalized)
        elif raw and str(raw).strip():
            logger.warning(
                "CORS origin rejected as invalid (value hidden): "
                "only absolute http(s) origins are allowed"
            )

    if not origins:
        logger.warning(
            "CORS allowed-origins list is empty; cross-origin browser "
            "requests will be denied until PUBLIC_BASE_URL/VITE_KC_URL "
            "or extra origins are configured"
        )

    return sorted(origins)
