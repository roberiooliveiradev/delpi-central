"""Ranking delta % de faturamento (KPI carteira comparativos T5)."""

from __future__ import annotations

import calendar
from typing import Any, Literal, Protocol

from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)

GroupBy = Literal["customer", "seller"]
RankingOrder = Literal["growth", "decline"]
NATURE_PORTFOLIO_BILLING_RANKING = "portfolio_billing_ranking"
BILLING_AMOUNT_NATURES = ("gross", "net")
DEFAULT_BILLING_AMOUNT_NATURE = "gross"


def normalize_billing_amount_nature(value: str | None) -> str:
    if not isinstance(value, str):
        value = None
    nature = (value or DEFAULT_BILLING_AMOUNT_NATURE).strip().lower()
    if nature not in BILLING_AMOUNT_NATURES:
        raise ValueError("nature inválida. Use gross ou net.")
    return nature


class CommercialAnalyticsGatewayPort(Protocol):
    def get_commercial_analytics(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload


def _item_amount(item: dict[str, Any] | None, *, nature: str) -> float:
    if not item:
        return 0.0
    nature = normalize_billing_amount_nature(nature)
    if nature == "gross" and item.get("gross_revenue") is not None:
        return _as_float(item.get("gross_revenue"))
    return _as_float(item.get("rol"))


def shift_iso_date_by_years(iso_date: str, years: int) -> str:
    """Shift YYYY-MM-DD by whole years; clamp day for shorter months."""
    if not iso_date or len(iso_date) < 10:
        return iso_date
    try:
        y = int(iso_date[0:4])
        m = int(iso_date[5:7])
        d = int(iso_date[8:10])
    except ValueError:
        return iso_date
    target_y = y + years
    max_day = calendar.monthrange(target_y, m)[1]
    day = min(d, max_day)
    return f"{target_y:04d}-{m:02d}-{day:02d}"


def compute_delta_pct(current: float, prior: float) -> float | None:
    if prior <= 0:
        return None
    return round(((current - prior) / prior) * 100, 1)


def _items_map(raw: Any) -> dict[tuple[str, str], dict[str, Any]]:
    data = _unwrap_data(raw)
    if not isinstance(data, dict):
        return {}
    items = data.get("items")
    if not isinstance(items, list):
        return {}
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("customer_code") or "").strip()
        store = str(item.get("customer_store") or "").strip() or "01"
        if not code:
            continue
        out[(code, store)] = item
    return out


def _totvs_params(
    scope: CommercialCustomerScope,
    base: dict[str, object | None],
) -> dict[str, object]:
    params: dict[str, object] = {
        key: value
        for key, value in base.items()
        if value is not None and value != ""
    }
    codes = AnalyticsCustomerCodesService.codes_param(scope)
    if codes is not None:
        params["customer_codes"] = codes
    return params


class GetPortfolioBillingRankingUseCase:
    """Delta % ROL por cliente (escopo) vs período −1 ano; group_by seller opcional no caller."""

    def execute(
        self,
        gateway: CommercialAnalyticsGatewayPort,
        portfolio_scope: CommercialCustomerScope,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        customer_segment: str | None = None,
        limit: int = 50,
        group_by: GroupBy = "customer",
        order: RankingOrder = "growth",
        seller_name_by_customer: dict[tuple[str, str], str] | None = None,
        nature: str | None = None,
    ) -> dict[str, Any]:
        if not start_date or not end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        amount_nature = normalize_billing_amount_nature(nature)
        resolved_order: RankingOrder = "decline" if order == "decline" else "growth"
        prior_start = shift_iso_date_by_years(start_date, -1)
        prior_end = shift_iso_date_by_years(end_date, -1)
        base_current: dict[str, object | None] = {
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
            "customer_segment": customer_segment,
            "limit": min(max(int(limit), 1), 500),
            "include_others": False,
        }
        base_prior = {
            **base_current,
            "start_date": prior_start,
            "end_date": prior_end,
        }
        current_raw = gateway.get_commercial_analytics(
            "/rol/by-customer",
            params=_totvs_params(portfolio_scope, base_current),
        )
        prior_raw = gateway.get_commercial_analytics(
            "/rol/by-customer",
            params=_totvs_params(portfolio_scope, base_prior),
        )
        current_map = _items_map(current_raw)
        prior_map = _items_map(prior_raw)
        keys = set(current_map) | set(prior_map)

        if group_by == "seller":
            rows = self._rank_sellers(
                keys,
                current_map,
                prior_map,
                seller_name_by_customer or {},
                nature=amount_nature,
            )
        else:
            rows = self._rank_customers(
                keys, current_map, prior_map, nature=amount_nature
            )

        if resolved_order == "decline":
            rows.sort(
                key=lambda row: (
                    row["deltaPct"] is None,
                    row["deltaPct"] if row["deltaPct"] is not None else 0.0,
                    float(row["currentRol"]),
                )
            )
        else:
            rows.sort(
                key=lambda row: (
                    row["deltaPct"] is None,
                    -(row["deltaPct"] if row["deltaPct"] is not None else 0.0),
                    -float(row["currentRol"]),
                )
            )
        for index, row in enumerate(rows, start=1):
            row["rank"] = index

        return {
            "groupBy": group_by,
            "order": resolved_order,
            "items": rows[: min(max(int(limit), 1), 500)],
            "startDate": start_date,
            "endDate": end_date,
            "priorStartDate": prior_start,
            "priorEndDate": prior_end,
            "branch": branch,
            "nature": amount_nature,
            "billingNature": amount_nature,
            "kpiNature": NATURE_PORTFOLIO_BILLING_RANKING,
            "supportedNatures": list(BILLING_AMOUNT_NATURES),
        }

    def _rank_customers(
        self,
        keys: set[tuple[str, str]],
        current_map: dict[tuple[str, str], dict[str, Any]],
        prior_map: dict[tuple[str, str], dict[str, Any]],
        *,
        nature: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key in keys:
            cur = current_map.get(key)
            pri = prior_map.get(key)
            current_rol = _item_amount(cur, nature=nature)
            prior_rol = _item_amount(pri, nature=nature)
            name = ""
            if cur and cur.get("customer_name"):
                name = str(cur.get("customer_name"))
            elif pri and pri.get("customer_name"):
                name = str(pri.get("customer_name"))
            delta = round(current_rol - prior_rol, 2)
            rows.append(
                {
                    "customerCode": key[0],
                    "customerStore": key[1],
                    "customerName": name,
                    "sellerName": None,
                    "currentRol": round(current_rol, 2),
                    "priorRol": round(prior_rol, 2),
                    "delta": delta,
                    "deltaPct": compute_delta_pct(current_rol, prior_rol),
                }
            )
        return rows

    def _rank_sellers(
        self,
        keys: set[tuple[str, str]],
        current_map: dict[tuple[str, str], dict[str, Any]],
        prior_map: dict[tuple[str, str], dict[str, Any]],
        seller_name_by_customer: dict[tuple[str, str], str],
        *,
        nature: str,
    ) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, float]] = {}
        for key in keys:
            seller = seller_name_by_customer.get(key) or "Sem vendedor"
            cur = current_map.get(key)
            pri = prior_map.get(key)
            current_rol = _item_amount(cur, nature=nature)
            prior_rol = _item_amount(pri, nature=nature)
            bucket = buckets.setdefault(seller, {"current": 0.0, "prior": 0.0})
            bucket["current"] += current_rol
            bucket["prior"] += prior_rol
        rows: list[dict[str, Any]] = []
        for seller_name, totals in buckets.items():
            current_rol = totals["current"]
            prior_rol = totals["prior"]
            rows.append(
                {
                    "customerCode": None,
                    "customerStore": None,
                    "customerName": None,
                    "sellerName": seller_name,
                    "currentRol": round(current_rol, 2),
                    "priorRol": round(prior_rol, 2),
                    "delta": round(current_rol - prior_rol, 2),
                    "deltaPct": compute_delta_pct(current_rol, prior_rol),
                }
            )
        return rows
