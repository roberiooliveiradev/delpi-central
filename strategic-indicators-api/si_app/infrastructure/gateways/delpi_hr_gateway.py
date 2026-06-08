from __future__ import annotations

from delpi_api_client import DelpiApiClient

from delpi_domain.hr_snapshot import HrMetricsSnapshot, parse_hr_snapshot_payload
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context


class DelpiHrGateway:
    """Indicadores de RH via api-delpi (`GET /hr/snapshot`)."""

    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple[str, str, str], HrMetricsSnapshot] = {}

    def get_snapshot(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> HrMetricsSnapshot:
        key = (branch or "", start_date or "", end_date or "")
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        data = self._client.get_hr_snapshot(
            params={
                "branch": branch,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=bearer_authorization_from_context(),
        )
        snapshot = parse_hr_snapshot_payload(data)
        self._cache[key] = snapshot
        return snapshot
