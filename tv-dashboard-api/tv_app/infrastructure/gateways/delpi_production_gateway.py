from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization


class DelpiProductionGateway:
    def __init__(self, client: DelpiApiClient | None = None) -> None:
        self._client = client or DelpiApiClient()

    def fetch_oee_overview(
        self,
        *,
        branch: str | None,
        period_days: int,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        end = date.today()
        start = end - timedelta(days=max(period_days, 1))
        params = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "branch": branch,
        }
        auth = authorization or internal_service_authorization()
        envelope = self._client.get_overall_equipment_effectiveness(
            params={k: v for k, v in params.items() if v},
            authorization=auth,
        )
        data = envelope.get("data") if isinstance(envelope, dict) else envelope
        summary = {}
        if isinstance(data, dict):
            summary = data.get("summary") or data
        return {
            "branch": branch,
            "periodDays": period_days,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "oeePct": summary.get("value") or summary.get("oeePct") or summary.get("oee_pct"),
            "targetPct": summary.get("target") or summary.get("targetPct") or summary.get("target_pct"),
            "status": summary.get("status"),
            "label": summary.get("label") or "OEE",
        }
