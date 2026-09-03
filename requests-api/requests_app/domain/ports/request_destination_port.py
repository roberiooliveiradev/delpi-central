from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from requests_app.domain.entities import Request


@dataclass(slots=True)
class DeliveryResult:
    ok: bool
    detail: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class RequestDestinationPort(ABC):
    """Outbound delivery / health for a request type destination adapter."""

    adapter_name: str = ""

    @abstractmethod
    def health(self) -> DeliveryResult:
        """Lightweight connectivity check for the destination."""

    @abstractmethod
    def deliver(
        self,
        *,
        request: Request,
        event_type: str,
        payload: dict[str, Any],
    ) -> DeliveryResult:
        """Deliver a side-effect payload to the destination (stub until verticals)."""
