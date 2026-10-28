"""Use case — matriz de faturamento por cliente × mês."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.application.dto.commercial.get_billing_by_customer_month_request import (
    GetBillingByCustomerMonthRequest,
)
from app.domain.entities.commercial.billing_by_customer_month import (
    BillingByCustomerMonthItem,
    BillingByCustomerMonthResult,
)
from app.domain.ports.commercial.commercial_billing_by_customer_month_repository_port import (
    CommercialBillingByCustomerMonthRepositoryPort,
)


def _parse_iso(value: str) -> date:
    return date.fromisoformat(str(value).strip())


def _month_keys(start: date, end: date) -> tuple[str, ...]:
    keys: list[str] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        keys.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return tuple(keys)


def _protheus_ym_to_iso(raw: object) -> str | None:
    text = str(raw or "").strip()
    if len(text) >= 6 and text[:6].isdigit():
        return f"{text[:4]}-{text[4:6]}"
    if len(text) == 7 and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit():
        return text
    return None


class GetBillingByCustomerMonthUseCase:
    def __init__(
        self,
        repository: CommercialBillingByCustomerMonthRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        request: GetBillingByCustomerMonthRequest,
    ) -> BillingByCustomerMonthResult:
        request.validate()
        start = _parse_iso(str(request.start_date))
        end = _parse_iso(str(request.end_date))
        if start > end:
            raise ValueError("start_date não pode ser posterior a end_date.")
        # Clamp end to last day of month for key generation consistency.
        _ = monthrange(end.year, end.month)
        months = _month_keys(start, end)
        month_set = set(months)

        rows = self._repository.list_billing_rows(request)
        by_customer: dict[tuple[str, str], dict] = {}
        for row in rows:
            code = str(row.get("customer_code") or "").strip()
            store = str(row.get("customer_store") or "").strip() or "01"
            if not code:
                continue
            ym = _protheus_ym_to_iso(row.get("year_month"))
            if not ym or ym not in month_set:
                continue
            key = (code, store)
            current = by_customer.get(key)
            value = float(row.get("billed_value") or 0.0)
            if current is None:
                by_customer[key] = {
                    "customer_code": code,
                    "customer_store": store,
                    "customer_name": str(
                        row.get("customer_name") or code
                    ).strip()
                    or code,
                    "monthly_values": {m: 0.0 for m in months},
                    "total": 0.0,
                }
                current = by_customer[key]
            current["monthly_values"][ym] = round(
                float(current["monthly_values"].get(ym, 0.0)) + value,
                2,
            )
            current["total"] = round(float(current["total"]) + value, 2)

        ordered = sorted(
            by_customer.values(),
            key=lambda item: (-float(item["total"]), item["customer_code"], item["customer_store"]),
        )
        truncated = len(ordered) > int(request.limit)
        if truncated:
            ordered = ordered[: int(request.limit)]

        items = tuple(
            BillingByCustomerMonthItem(
                customer_code=item["customer_code"],
                customer_store=item["customer_store"],
                customer_name=item["customer_name"],
                monthly_values=dict(item["monthly_values"]),
                total=float(item["total"]),
            )
            for item in ordered
        )
        monthly_totals = {m: 0.0 for m in months}
        grand_total = 0.0
        for item in items:
            grand_total = round(grand_total + item.total, 2)
            for month_key, value in item.monthly_values.items():
                monthly_totals[month_key] = round(
                    monthly_totals.get(month_key, 0.0) + float(value),
                    2,
                )

        return BillingByCustomerMonthResult(
            branch=request.branch or "consolidated",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            nature=request.nature,
            months=months,
            items=items,
            grand_total=grand_total,
            monthly_totals=monthly_totals,
            customers_count=len(items),
            truncated=truncated,
        )
