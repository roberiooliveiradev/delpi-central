from __future__ import annotations

from app.application.ports.platform_access_port import (
    AuthenticationError,
    AuthorityUnavailableError,
)
from app.application.platform_access import (
    PlatformAccessContext,
    platform_access_from_core_me,
)


class CorePlatformAccessAdapter:
    """JWT validate (shared validator) + Core GET /me. Fail closed. No JWT AuthZ."""

    def __init__(self, *, core_api_url: str, timeout_seconds: float, http_get) -> None:
        self._core_api_url = core_api_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._http_get = http_get

    def resolve(self, bearer_token: str) -> PlatformAccessContext:
        token = (bearer_token or "").strip()
        if not token:
            raise AuthenticationError("missing_token")

        self._validate_token(token)
        payload = self._fetch_core_me(token)
        try:
            return platform_access_from_core_me(payload)
        except ValueError as exc:
            raise AuthorityUnavailableError("core_malformed_response") from exc

    def _validate_token(self, token: str) -> None:
        # Import at call boundary so Application never imports delpi_auth.
        from delpi_auth.jwt_validator import JwtConfigurationError, validate_token

        try:
            validate_token(token)
        except JwtConfigurationError as exc:
            raise AuthenticationError("jwt_configuration_error") from exc
        except Exception as exc:
            raise AuthenticationError("invalid_token") from exc

    def _fetch_core_me(self, token: str) -> dict:
        url = f"{self._core_api_url}/me"
        try:
            response = self._http_get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self._timeout_seconds,
            )
        except Exception as exc:
            raise AuthorityUnavailableError("core_unavailable") from exc

        status = getattr(response, "status_code", None)
        if status in {401, 403}:
            raise AuthenticationError("core_rejected_token")
        if status != 200:
            raise AuthorityUnavailableError("core_unavailable")

        try:
            payload = response.json()
        except Exception as exc:
            raise AuthorityUnavailableError("core_malformed_response") from exc

        if not isinstance(payload, dict):
            raise AuthorityUnavailableError("core_malformed_response")
        return payload
