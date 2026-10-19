# shared/delpi_auth/cors_policy.py
"""Canonical CORS origin policy for Minha DELPI HTTP services.

Platform rule (platform-security-identity-authorization.mdc): CORS is
restrictive — only explicitly authorized origins receive CORS headers.
This module is the single source that builds the allowlist:

- ``PUBLIC_BASE_URL`` (portal/gateway public origin)
- ``VITE_KC_URL`` (Keycloak origin, ``/auth`` suffix stripped)
- ``http://localhost`` only when the resolved environment is not
  ``production`` (``API_DELPI_ENV``); it is never added in production.
- app-owned extras (e.g. Custom GPT origins) passed explicitly.

Never produces a wildcard. When the resulting list is empty, callers must
pass it through unchanged — Starlette/python-socketio then deny every
cross-origin browser request while same-origin and server-to-server
traffic keep working.
"""

import logging
import os
from collections.abc import Iterable, Mapping
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

LOCALHOST_ORIGIN = "http://localhost"
_PRODUCTION_ENV = "production"
_ALLOWED_SCHEMES = frozenset({"http", "https"})


def normalize_origin(value: "str | None") -> "str | None":
    """Return a normalized ``scheme://host[:port]`` origin or ``None``.

    Rejects empty values, wildcards, malformed URLs and non-HTTP(S)
    schemes so a bad env value can never widen access.
    """
    if not value:
        return None
    candidate = str(value).strip().rstrip("/")
    if not candidate or candidate == "*":
        return None
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return None
    if parts.scheme.lower() not in _ALLOWED_SCHEMES or not parts.netloc:
        return None
    return candidate


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
            ``API_DELPI_ENV`` (default ``development``).
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
        else env_map.get("API_DELPI_ENV", "development")
    )
    is_production = str(resolved_env).strip().lower() == _PRODUCTION_ENV

    origins: set[str] = set()
    for raw in (public_base_url, _keycloak_origin(keycloak_url)):
        normalized = normalize_origin(raw)
        if normalized:
            origins.add(normalized)

    if not is_production:
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
