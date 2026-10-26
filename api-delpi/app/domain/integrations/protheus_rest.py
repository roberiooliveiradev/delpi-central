"""Domain types for the Protheus REST integration (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_PARAM_KEYS = (
    "USR_PROTHEUS",
    "PSW_PROTHEUS",
    "URL_REST",
    "PATH_AUTH",
    "PATH_SUPPLIERS",
)

# Optional keys — fetched when present, never required (backward compatible).
OPTIONAL_PARAM_KEYS = ("BASE_PATH",)

SUPPLIER_ID_PATTERN = r"^[0-9]{8}$"
SUPPLIER_CODE_LENGTH = 6
SUPPLIER_STORE_LENGTH = 2
TOKEN_EXPIRY_MARGIN_SECONDS = 60


@dataclass(frozen=True, slots=True)
class ProtheusRestConfig:
    """Resolved technical configuration for Protheus REST calls."""

    username: str
    password: str
    base_url: str
    auth_path: str
    suppliers_path: str
    path_label_mismatch: bool = False

    @property
    def auth_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.auth_path.lstrip('/')}"

    @property
    def suppliers_base_url(self) -> str:
        base = f"{self.base_url.rstrip('/')}/{self.suppliers_path.lstrip('/')}"
        return base if base.endswith("/") else f"{base}/"


@dataclass(frozen=True, slots=True)
class ProtheusAccessToken:
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    obtained_at_monotonic: float = 0.0


@dataclass(frozen=True, slots=True)
class ProtheusIntegrationStatus:
    """Sanitized integration diagnostic — safe to expose to authorized clients.

    Never carries URLs, tokens, credentials or internal hosts; states are
    coarse labels plus the upstream HTTP status observed on authentication.
    """

    integration: str
    configuration: str
    authentication: str
    connection: str
    config_path_label_mismatch: bool = False
    transport: str = "unknown"
    checked_at: str = ""
    environment: str = "unknown"
    connectivity: str = "not_checked"
    authentication_http_status: int | None = None
    suppliers_read: str = "not_checked"
    create_gate: str = "disabled"
    update_gate: str = "disabled"
    write_target_guard: str = "unverified"
    write_validation: str = "not_tested"
    overall: str = "unavailable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "integration": self.integration,
            "configuration": self.configuration,
            "authentication": self.authentication,
            "connection": self.connection,
            "config_path_label_mismatch": self.config_path_label_mismatch,
            "transport": self.transport,
            "checked_at": self.checked_at,
            "environment": self.environment,
            "connectivity": self.connectivity,
            "authentication_http_status": self.authentication_http_status,
            "suppliers_read": self.suppliers_read,
            "create_gate": self.create_gate,
            "update_gate": self.update_gate,
            "write_target_guard": self.write_target_guard,
            "write_validation": self.write_validation,
            "overall": self.overall,
        }


class ProtheusRestError(Exception):
    """Controlled Protheus REST integration failure (safe for API clients)."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int = 502,
        recoverable: bool = True,
        upstream_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.recoverable = recoverable
        self.upstream_status = upstream_status
