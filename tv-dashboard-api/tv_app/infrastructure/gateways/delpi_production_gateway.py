from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization


def _extract_summary(envelope: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        return {}
    data = envelope.get("data")
    if isinstance(data, dict):
        summary = data.get("summary")
        if isinstance(summary, dict):
            return summary
        return data
    return {}


def _date_range(period_days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=max(period_days, 1))
    return start.isoformat(), end.isoformat()


class DelpiProductionGateway:
    def __init__(self, client: DelpiApiClient | None = None) -> None:
        self._client = client or DelpiApiClient()

    def _auth(self, authorization: str | None) -> str | None:
        return authorization or internal_service_authorization()

    def fetch_oee_overview(
        self,
        *,
        branch: str | None,
        period_days: int,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        start, end = _date_range(period_days)
        params = {"start_date": start, "end_date": end, "branch": branch}
        envelope = self._client.get_overall_equipment_effectiveness(
            params={k: v for k, v in params.items() if v},
            authorization=self._auth(authorization),
        )
        summary = _extract_summary(envelope)
        return {
            "branch": branch,
            "periodDays": period_days,
            "startDate": start,
            "endDate": end,
            "oeePct": summary.get("value") or summary.get("oeePct") or summary.get("oee_pct"),
            "targetPct": summary.get("target") or summary.get("targetPct") or summary.get("target_pct"),
            "status": summary.get("status"),
            "label": summary.get("label") or "OEE",
        }

    def fetch_otd_summary(
        self,
        *,
        branch: str | None,
        period_days: int,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        start, end = _date_range(period_days)
        params = {"start_date": start, "end_date": end, "branch": branch}
        envelope = self._client.get_on_time_delivery(
            params={k: v for k, v in params.items() if v},
            authorization=self._auth(authorization),
        )
        summary = _extract_summary(envelope)
        return {
            "branch": branch,
            "periodDays": period_days,
            "startDate": start,
            "endDate": end,
            "otdPct": summary.get("value") or summary.get("otdPct") or summary.get("otd_pct"),
            "targetPct": summary.get("target") or summary.get("targetPct"),
            "label": summary.get("label") or "OTD Produção",
        }

    def fetch_ppm_summary(
        self,
        *,
        branch: str | None,
        period_days: int,
        ppm_type: str = "internal",
        authorization: str | None = None,
    ) -> dict[str, Any]:
        start, end = _date_range(period_days)
        ppm = (ppm_type or "internal").strip().lower()
        if ppm not in {"internal", "external"}:
            ppm = "internal"
        params = {"start_date": start, "end_date": end, "branch": branch}
        envelope = self._client.get_ppm_summary(
            ppm,
            params={k: v for k, v in params.items() if v},
            authorization=self._auth(authorization),
        )
        summary = _extract_summary(envelope)
        return {
            "branch": branch,
            "periodDays": period_days,
            "ppmType": ppm,
            "startDate": start,
            "endDate": end,
            "ppmValue": summary.get("value") or summary.get("ppm") or summary.get("ppmValue"),
            "targetPct": summary.get("target") or summary.get("targetPct"),
            "label": summary.get("label") or f"PPM {ppm}",
        }

    def fetch_stock_value_summary(
        self,
        *,
        branch: str | None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params = {"branch": branch} if branch else None
        envelope = self._client.get_stock_value(
            params=params,
            authorization=self._auth(authorization),
        )
        summary = _extract_summary(envelope)
        return {
            "branch": branch,
            "stockValue": summary.get("value") or summary.get("stockValue") or summary.get("total"),
            "label": summary.get("label") or "Valor de estoque",
            "currency": summary.get("currency") or "BRL",
        }
