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
    integration: str
    configuration: str
    authentication: str
    connection: str
    config_path_label_mismatch: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "integration": self.integration,
            "configuration": self.configuration,
            "authentication": self.authentication,
            "connection": self.connection,
            "config_path_label_mismatch": self.config_path_label_mismatch,
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
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.recoverable = recoverable
