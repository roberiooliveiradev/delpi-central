"""Port for catalog-fixed GET execution (transport adapter; not Application)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class CatalogFixedGetRequest:
    """Transport-agnostic request produced by Application after validation."""

    action_id: str
    method: Literal["GET"]
    path: str
    query: dict[str, Any]


@dataclass(frozen=True)
class CatalogFixedGetResult:
    """Transport outcome without exposing HTTP client types to Application."""

    outcome: Literal["ok", "unauthorized", "forbidden", "error"]
    payload: Any = None
    error_message: str | None = None


class CatalogFixedGetPort(Protocol):
    def execute(
        self,
        request: CatalogFixedGetRequest,
        *,
        authorization: str,
    ) -> CatalogFixedGetResult: ...
