from __future__ import annotations

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient

_LARGE_PAGE = 5000


class DelpiEngineeringGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_lmp_dashboard_rows(
        self,
        *,
        date_start: str | None,
        date_end: str | None,
        branch: str | None,
        include_qtd_pi: bool = False,
    ) -> list[dict]:
        params: dict[str, str | None] = {
            "date_start": date_start,
            "date_end": date_end,
            "branch": branch,
            "listing_type": "lmp",
            "page": "1",
            "page_size": str(_LARGE_PAGE),
        }
        if include_qtd_pi:
            params["include_qtd_pi"] = "true"

        data = self._client.list_lmps(
            params=params,
            authorization=bearer_authorization_from_context(),
        )
        items_raw = data.get("items") or []
        return [
            {
                "branch": it.get("branch"),
                "sale_number": it.get("sale_number"),
                "start_date": it.get("start_date"),
                "end_date": it.get("end_date"),
                "engineering_status": it.get("engineering_status"),
                "engineering_total_minutes": int(it.get("engineering_total_minutes") or 0),
                "qtd_pi": int(it.get("qtd_pi") or 0),
            }
            for it in items_raw
        ]

    def get_computed_dashboard_summary(
        self,
        *,
        date_start: str | None,
        date_end: str | None,
        branch: str | None,
    ) -> dict[str, float | int | None]:
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
