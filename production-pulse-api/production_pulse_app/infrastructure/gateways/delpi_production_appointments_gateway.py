from __future__ import annotations

from typing import Any

from delpi_api_client import DelpiApiClient, DelpiApiError

from production_pulse_app.config import settings


class DelpiProductionAppointmentsGateway:
    def __init__(self, client: DelpiApiClient | None = None) -> None:
        self._client = client or DelpiApiClient(
            base_url=settings.DELPI_API_URL,
            timeout=settings.DELPI_API_TIMEOUT,
            caller_app=settings.DELPI_API_CALLER_APP,
        )

    def list_work_centers(
        self,
        *,
        branch: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self._client.list_production_appointment_work_centers(
                params={"branch": branch},
                authorization=authorization,
            )
        except DelpiApiError:
            raise


__all__ = ["DelpiApiError", "DelpiProductionAppointmentsGateway"]
