from __future__ import annotations

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


class DelpiEngineeringGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_lmp_dashboard_summary(
        self,
        *,
        date_start: str | None,
        date_end: str | None,
        branch: str | None,
    ) -> dict[str, float | int]:
        data = self._client.get_lmp_dashboard_summary(
            params={
                "date_start": date_start,
                "date_end": date_end,
                "branch": branch,
            },
            authorization=bearer_authorization_from_context(),
        )
        return {
            "total_lmps": int(data.get("total_lmps") or 0),
            "percent_dentro_prazo": float(data.get("percent_dentro_prazo") or 0.0),
            "avg_lead_time": float(data.get("avg_lead_time") or 0.0),
        }

    def get_transforma_mais_summary(
        self,
        *,
        filial_id: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        return self._client.get_transforma_mais_summary(
            params={
                "filial_id": filial_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=bearer_authorization_from_context(),
        )
