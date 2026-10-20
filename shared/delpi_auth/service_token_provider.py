"""Client-credentials token provider for service-to-service calls.

Requests an OAuth2 Client Credentials token from the configured issuer
token endpoint, caches it in memory with an early-refresh margin and fails
with typed errors. The client secret and issued tokens are never logged —
callers should log error codes, not exceptions containing payloads.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

import requests

from .service_errors import (
    ServiceAuthConfigError,
    ServiceTokenRequestError,
    ServiceTokenResponseError,
)

S2S_TOKEN_URL_ENV = "S2S_TOKEN_URL"
S2S_CLIENT_ID_ENV = "S2S_CLIENT_ID"
S2S_CLIENT_SECRET_ENV = "S2S_CLIENT_SECRET"
S2S_SCOPE_ENV = "S2S_SCOPE"
S2S_TIMEOUT_SECONDS_ENV = "S2S_TIMEOUT_SECONDS"

_DEFAULT_TIMEOUT_SECONDS = 10.0
_DEFAULT_REFRESH_MARGIN_SECONDS = 30.0
_FALLBACK_EXPIRES_IN_SECONDS = 60.0

HttpPost = Callable[..., "requests.Response"]


@dataclass(frozen=True)
class ServiceTokenProviderConfig:
    token_url: str
    client_id: str
    client_secret: str
    scopes: tuple[str, ...] = ()
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "ServiceTokenProviderConfig":
        env = environ if environ is not None else os.environ
        token_url = (env.get(S2S_TOKEN_URL_ENV) or "").strip()
        client_id = (env.get(S2S_CLIENT_ID_ENV) or "").strip()
        client_secret = (env.get(S2S_CLIENT_SECRET_ENV) or "").strip()
        missing = []
        if not token_url:
            missing.append(S2S_TOKEN_URL_ENV)
        if not client_id:
            missing.append(S2S_CLIENT_ID_ENV)
        if not client_secret:
            missing.append(S2S_CLIENT_SECRET_ENV)
        if missing:
            raise ServiceAuthConfigError(
                "Missing S2S provider configuration: " + ", ".join(missing)
            )
        scopes = tuple(
            item for item in (env.get(S2S_SCOPE_ENV) or "").split() if item
        )
        try:
            timeout_seconds = float(
                (env.get(S2S_TIMEOUT_SECONDS_ENV) or "").strip()
                or _DEFAULT_TIMEOUT_SECONDS
            )
        except ValueError as exc:
            raise ServiceAuthConfigError(
                f"{S2S_TIMEOUT_SECONDS_ENV} must be a number"
            ) from exc
        return cls(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            timeout_seconds=timeout_seconds,
        )


class ClientCredentialsTokenProvider:
    """OAuth2 Client Credentials provider with in-memory expiry-aware cache."""

    def __init__(
        self,
        config: ServiceTokenProviderConfig,
        *,
        http_post: HttpPost | None = None,
        clock: Callable[[], float] = time.time,
        refresh_margin_seconds: float = _DEFAULT_REFRESH_MARGIN_SECONDS,
    ) -> None:
        self._config = config
        self._http_post = http_post or requests.post
        self._clock = clock
        self._refresh_margin = max(0.0, float(refresh_margin_seconds))
        self._lock = threading.Lock()
        self._cached: tuple[str, float] | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None, **kwargs):
        return cls(ServiceTokenProviderConfig.from_env(environ), **kwargs)

    def get_token(self) -> str:
        with self._lock:
            if self._cached is not None:
                token, usable_until = self._cached
                if self._clock() < usable_until:
                    return token
            self._cached = self._request_token()
            return self._cached[0]

    def invalidate(self) -> None:
        with self._lock:
            self._cached = None

    def _request_token(self) -> tuple[str, float]:
        form = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        if self._config.scopes:
            form["scope"] = " ".join(self._config.scopes)

        try:
            response = self._http_post(
                self._config.token_url,
                data=form,
                timeout=self._config.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise ServiceTokenRequestError("S2S token endpoint unreachable") from exc

        status_code = getattr(response, "status_code", None)
        if status_code != 200:
            raise ServiceTokenRequestError(
                "S2S token endpoint rejected the grant",
                status_code=status_code if isinstance(status_code, int) else None,
            )

        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise ServiceTokenResponseError("S2S token response is not JSON") from exc
        if not isinstance(payload, dict):
            raise ServiceTokenResponseError("S2S token response is not an object")

        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise ServiceTokenResponseError("S2S token response lacks access_token")

        try:
            expires_in = float(payload.get("expires_in") or _FALLBACK_EXPIRES_IN_SECONDS)
        except (TypeError, ValueError):
            expires_in = _FALLBACK_EXPIRES_IN_SECONDS
        if expires_in <= 0:
            expires_in = _FALLBACK_EXPIRES_IN_SECONDS

        usable_until = self._clock() + max(0.0, expires_in - self._refresh_margin)
        return access_token, usable_until
