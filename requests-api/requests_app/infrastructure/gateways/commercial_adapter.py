from __future__ import annotations

from typing import Any

from requests_app.domain.entities import Request
from requests_app.domain.ports.request_destination_port import (
    DeliveryResult,
    RequestDestinationPort,
)


class CommercialAdapter(RequestDestinationPort):
    """Stub for future commercial-api destinations (no HTTP in E4)."""

    adapter_name = "commercial"

    def health(self) -> DeliveryResult:
        return DeliveryResult(ok=True, detail="commercial adapter stub")

    def deliver(
        self,
        *,
        request: Request,
        event_type: str,
        payload: dict[str, Any],
    ) -> DeliveryResult:
        return DeliveryResult(
            ok=True,
            detail="commercial deliver stub",
            meta={
                "request_id": str(request.id),
                "event_type": event_type,
                "payload_keys": sorted(payload.keys()),
            },
        )
