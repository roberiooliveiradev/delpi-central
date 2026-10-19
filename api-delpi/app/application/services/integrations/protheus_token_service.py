"""In-process Protheus OAuth token cache (no DB persistence in this delivery)."""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Callable

from app.domain.integrations.protheus_rest import (
    TOKEN_EXPIRY_MARGIN_SECONDS,
    ProtheusAccessToken,
    ProtheusRestConfig,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway


class ProtheusTokenService:
    """Reuses a valid access token until near expiry; never exposes it to API clients."""

    def __init__(
        self,
        gateway: ProtheusRestGateway,
        *,
        expiry_margin_seconds: int = TOKEN_EXPIRY_MARGIN_SECONDS,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._gateway = gateway
        self._expiry_margin_seconds = max(0, expiry_margin_seconds)
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._cached: ProtheusAccessToken | None = None
        self._cached_auth_fingerprint: str | None = None

    def get_valid_token(self, config: ProtheusRestConfig) -> str:
        fingerprint = config_auth_fingerprint(config)
        with self._lock:
            if (
                self._cached is not None
                and self._cached_auth_fingerprint == fingerprint
                and self._is_fresh(self._cached)
            ):
                return self._cached.access_token

            token = self._gateway.request_access_token(config)
            self._cached = token
            self._cached_auth_fingerprint = fingerprint
            return token.access_token

    def invalidate(self) -> None:
        with self._lock:
            self._cached = None
            self._cached_auth_fingerprint = None

    def _is_fresh(self, token: ProtheusAccessToken) -> bool:
        age = self._monotonic() - float(token.obtained_at_monotonic or 0.0)
        return age < max(1, int(token.expires_in) - self._expiry_margin_seconds)


def config_auth_fingerprint(config: ProtheusRestConfig) -> str:
    """Stable auth identity without storing plaintext password.

    Includes a SHA-256 digest of the password so credential rotation
    invalidates the in-memory token cache. The digest is never logged.
    """
    password_digest = hashlib.sha256(
        config.password.encode("utf-8")
    ).hexdigest()
    return f"{config.username}|{config.auth_url}|{password_digest}"
