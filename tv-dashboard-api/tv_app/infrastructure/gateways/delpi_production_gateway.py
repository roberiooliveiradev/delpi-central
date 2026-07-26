from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization

from tv_app.application.services.series_points_extractor import (
    envelope_data,
    extract_series_points,
)


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


def _series_query_params(*, start: str, end: str, branch: str | None) -> dict[str, str]:
    params: dict[str, str] = {
        "start_date": start,
        "end_date": end,
        "granularity": "day",
    }
    if branch:
        params["branch"] = branch
    return params


class DelpiProductionGateway:
    def __init__(self, client: DelpiApiClient | None = None) -> None:
        self._client = client or DelpiApiClient()

    def _auth(self, authorization: str | None) -> str | None:
        return authorization or internal_service_authorization()

    def _fetch_series_points(
        self,
        *,
        fetch,
        branch: str | None,
        start: str,
        end: str,
        authorization: str | None,
    ) -> list[dict[str, Any]]:
        try:
            envelope = fetch(
                params=_series_query_params(start=start, end=end, branch=branch),
                authorization=self._auth(authorization),
            )
            return extract_series_points(envelope_data(envelope), "points", branch=branch)
        except Exception:  # noqa: BLE001 — KPI dual permanece mesmo se a série falhar
            return []

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
        points = self._fetch_series_points(
            fetch=self._client.get_production_oee_series,
            branch=branch,
            start=start,
            end=end,
            authorization=authorization,
        )
        return {
            "branch": branch,
            "periodDays": period_days,
            "startDate": start,
            "endDate": end,
            "oeePct": summary.get("value") or summary.get("oeePct") or summary.get("oee_pct"),
            "targetPct": summary.get("target") or summary.get("targetPct") or summary.get("target_pct"),
            "status": summary.get("status"),
            "label": summary.get("label") or "OEE",
            "seriesPoints": points,
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
        points = self._fetch_series_points(
            fetch=self._client.get_production_otd_series,
            branch=branch,
            start=start,
            end=end,
            authorization=authorization,
        )
        return {
            "branch": branch,
            "periodDays": period_days,
            "startDate": start,
            "endDate": end,
            "otdPct": summary.get("value") or summary.get("otdPct") or summary.get("otd_pct"),
            "targetPct": summary.get("target") or summary.get("targetPct"),
            "label": summary.get("label") or "OTD Produção",
            "seriesPoints": points,
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
        series_params: dict[str, str] = {
            "start_date": start,
            "end_date": end,
            "granularity": "day",
        }
        if branch:
            series_params["branch"] = branch
        try:
            series_envelope = self._client.get_ppm_series(
                ppm,
                params=series_params,
                authorization=self._auth(authorization),
            )
            points = extract_series_points(
                envelope_data(series_envelope), "points", branch=branch
            )
        except Exception:  # noqa: BLE001 — KPI dual permanece mesmo se a série falhar
            points = []
        return {
            "branch": branch,
            "periodDays": period_days,
            "ppmType": ppm,
            "startDate": start,
            "endDate": end,
            "ppmValue": summary.get("value") or summary.get("ppm") or summary.get("ppmValue"),
            "targetPct": summary.get("target") or summary.get("targetPct"),
            "label": summary.get("label") or f"PPM {ppm}",
            "seriesPoints": points,
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

    def fetch_stock_alert(
        self,
        *,
        branch: str | None,
        item_limit: int = 6,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        limit = max(1, min(int(item_limit or 6), 6))
        params: dict[str, str] = {"top_limit": str(limit)}
        if branch:
            params["branch"] = branch
        envelope = self._client.get_stock_value(
            params=params,
            authorization=self._auth(authorization),
        )
        raw_items = envelope.get("top_products") if isinstance(envelope, dict) else []
        items: list[dict[str, Any]] = []
        if isinstance(raw_items, list):
            for row in raw_items[:limit]:
                if not isinstance(row, dict):
                    continue
                items.append(
                    {
                        "productCode": row.get("product_code") or row.get("productCode"),
                        "description": row.get("product_description") or row.get("description"),
                        "stockValue": row.get("total_stock_value") or row.get("stockValue"),
                        "stockQuantity": row.get("total_stock_quantity") or row.get("stockQuantity"),
                    }
                )
        return {
            "branch": branch,
            "itemLimit": limit,
            "items": items,
            "label": "Itens críticos de estoque",
        }
