from __future__ import annotations

from collections import defaultdict
from typing import Any

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.payload_mapping import (
    as_float,
    as_int,
    as_opt_str,
    as_str,
    clamp_page,
    clamp_page_size,
    map_pagination,
    map_period,
    map_sort,
    resolve_delinquency_gateway_period,
    unwrap_data,
)
from financial_app.application.services.response_cache import cached_fetch
from financial_app.core.security import FIN_DELINQUENCY_VIEW
from financial_app.domain.errors import FinancialError
from financial_app.domain.ports.financial_data_gateway import FinancialDataGateway
from financial_app.domain.services.branch_access_service import BranchAccessService


class InvalidDelinquencyQuery(FinancialError):
    """Filtro, ordenação ou paginação fora do catálogo de inadimplência."""


def _settings() -> dict[str, Any]:
    return load_content("delinquency.json")


class DelinquencyService:
    def __init__(
        self,
        gateway: FinancialDataGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def summary(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        start, end = self._prepare(user, start_date, end_date)
        scope = self._customer_scope(customer_code, store_code)
        if scope:
            return self._summary_for_customer(
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
                title_stats=None,
            )
        payload = self._cached(
            "summary",
            {"start": start, "end": end},
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_summary(start_date=start, end_date=end)
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "scopeNotice": str(_settings().get("scopeNotice") or ""),
            "totals": self._map_totals(payload.get("totais")),
            "indicators": self._map_indicators(payload.get("indicadores")),
        }

    def monthly(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        new_business_only: bool = False,
        refresh: bool = False,
    ) -> dict[str, Any]:
        start, end = self._prepare(user, start_date, end_date)
        payload = self._cached(
            "monthly",
            {
                "start": start,
                "end": end,
                "customer": customer_code,
                "store": store_code,
                "new": new_business_only,
            },
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_monthly(
                    start_date=start,
                    end_date=end,
                    customer_code=customer_code,
                    store_code=store_code,
                    new_business_only=new_business_only,
                )
            ),
            refresh=refresh,
        )
        items = [
            self._map_month(item)
            for item in payload.get("items") or []
            if isinstance(item, dict)
        ]
        return {"period": map_period(payload.get("periodo")), "items": items}

    def aging(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        start, end = self._prepare(user, start_date, end_date)
        scope = self._customer_scope(customer_code, store_code)
        if scope:
            return self._aging_for_customer(
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
                title_stats=None,
            )
        payload = self._cached(
            "aging",
            {"start": start, "end": end},
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_aging(start_date=start, end_date=end)
            ),
            refresh=refresh,
        )
        items = [
            self._map_aging(item)
            for item in payload.get("items") or []
            if isinstance(item, dict)
        ]
        items.sort(key=lambda item: (as_int(item.get("order"), 99), item.get("code") or ""))
        return {"period": map_period(payload.get("periodo")), "items": items}

    def customers(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str | None,
        search: str | None,
        only_with_delays: bool,
        refresh: bool = False,
    ) -> dict[str, Any]:
        start, end = self._prepare(user, start_date, end_date)
        cfg = _settings()
        page_n, size_n, sort_field, direction = self._resolve_list_query(
            cfg, "customers", page, page_size, sort_by, sort_dir
        )
        payload = self._cached(
            "customers",
            {
                "start": start,
                "end": end,
                "page": page_n,
                "size": size_n,
                "sort": sort_field,
                "dir": direction,
                "search": search,
                "late": only_with_delays,
            },
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_customers(
                    start_date=start,
                    end_date=end,
                    page=page_n,
                    page_size=size_n,
                    sort_by=sort_field,
                    sort_dir=direction,
                    search=search,
                    only_with_delays=only_with_delays,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "pagination": map_pagination(payload.get("pagination"), default_page_size=size_n),
            "sort": map_sort(payload.get("sort"), default_by=sort_field, default_dir=direction),
            "items": [
                self._map_customer(item)
                for item in payload.get("items") or []
                if isinstance(item, dict)
            ],
        }

    def dashboard(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str | None,
        only_with_delays: bool,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Painel completo em uma ida — evita paginação duplicada de títulos por cliente."""
        start, end = self._prepare(user, start_date, end_date)
        scope = self._customer_scope(customer_code, store_code)
        title_stats = None
        if scope:
            title_stats = self._collect_customer_title_stats(
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
            )

        monthly = self.monthly(
            user,
            start_date=start_date,
            end_date=end_date,
            customer_code=scope[0] if scope else None,
            store_code=scope[1] if scope else None,
            refresh=refresh,
        )
        customers = self.customers(
            user,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=scope[0] if scope else None,
            only_with_delays=only_with_delays,
            refresh=refresh,
        )
        if scope:
            summary = self._summary_for_customer(
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
                title_stats=title_stats,
            )
            aging = self._aging_for_customer(
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
                title_stats=title_stats,
            )
            customers = self._scope_customers_payload(
                customers,
                start,
                end,
                scope[0],
                scope[1],
                refresh=refresh,
            )
        else:
            summary = self.summary(
                user,
                start_date=start_date,
                end_date=end_date,
                refresh=refresh,
            )
            aging = self.aging(
                user,
                start_date=start_date,
                end_date=end_date,
                refresh=refresh,
            )

        top_delinquent = (
            self._top_delinquent_from_items(customers.get("items") or [])
            if scope
            else self._top_delinquent_customers(
                user,
                start_date=start_date,
                end_date=end_date,
                refresh=refresh,
            )
        )

        return {
            "summary": summary,
            "monthly": monthly,
            "aging": aging,
            "customers": customers,
            "topDelinquentCustomers": top_delinquent,
        }

    def titles(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None,
        store_code: str | None,
        status: str | None,
        delay_range: str | None,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str | None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        start, end = self._prepare(user, start_date, end_date)
        cfg = _settings()
        status_value = (status or "all").strip() or "all"
        allowed_status = {str(item) for item in cfg.get("titleStatuses") or []}
        if status_value not in allowed_status:
            raise InvalidDelinquencyQuery(str((cfg.get("messages") or {}).get("invalidStatus") or ""))
        range_value = as_opt_str(delay_range)
        allowed_ranges = {str(item) for item in cfg.get("agingRanges") or []}
        if range_value and range_value not in allowed_ranges:
            raise InvalidDelinquencyQuery(
                str((cfg.get("messages") or {}).get("invalidAgingRange") or "")
            )
        page_n, size_n, sort_field, direction = self._resolve_list_query(
            cfg, "titles", page, page_size, sort_by, sort_dir
        )
        payload = self._cached(
            "titles",
            {
                "start": start,
                "end": end,
                "customer": customer_code,
                "store": store_code,
                "status": status_value,
                "range": range_value,
                "search": search,
                "page": page_n,
                "size": size_n,
                "sort": sort_field,
                "dir": direction,
            },
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_titles(
                    start_date=start,
                    end_date=end,
                    customer_code=customer_code,
                    store_code=store_code,
                    status=status_value,
                    delay_range=range_value,
                    search=search,
                    page=page_n,
                    page_size=size_n,
                    sort_by=sort_field,
                    sort_dir=direction,
                )
            ),
            refresh=refresh,
        )
        return {
            "period": map_period(payload.get("periodo")),
            "pagination": map_pagination(payload.get("pagination"), default_page_size=size_n),
            "sort": map_sort(payload.get("sort"), default_by=sort_field, default_dir=direction),
            "filters": {
                "customerCode": as_opt_str(customer_code),
                "store": as_opt_str(store_code),
                "status": status_value,
                "delayRange": range_value,
                "search": as_opt_str(search),
            },
            "items": [
                self._map_title(item)
                for item in payload.get("items") or []
                if isinstance(item, dict)
            ],
        }

    def _prepare(
        self, user: object | None, start_date: str | None, end_date: str | None
    ) -> tuple[str | None, str | None]:
        self._branch_access.assert_can_use(user, FIN_DELINQUENCY_VIEW)
        self._branch_access.resolve_branch_scope(user, None)
        return resolve_delinquency_gateway_period(start_date, end_date)

    def _cached(
        self,
        kind: str,
        parts: dict[str, Any],
        loader,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((_settings().get("cacheTtlSeconds") or {}).get(kind), 0)
        key = f"delinquency:{kind}:{sorted(parts.items())}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    def _resolve_list_query(
        self,
        cfg: dict[str, Any],
        list_key: str,
        page: int | None,
        page_size: int | None,
        sort_by: str | None,
        sort_dir: str | None,
    ) -> tuple[int, int, str, str]:
        pagination = cfg.get("pagination") or {}
        sort_cfg = (cfg.get("sort") or {}).get(list_key) or {}
        allowed = {str(item) for item in sort_cfg.get("allowed") or []}
        default_by = str(sort_cfg.get("default") or next(iter(allowed), ""))
        field = (sort_by or default_by).strip() or default_by
        if field not in allowed:
            allowed_label = ", ".join(sorted(allowed))
            template = str((cfg.get("messages") or {}).get("invalidSortBy") or "Ordenação inválida.")
            raise InvalidDelinquencyQuery(template.format(allowed=allowed_label))
        directions = {str(item) for item in (cfg.get("sort") or {}).get("allowedDirections") or []}
        direction = (sort_dir or "desc").strip().lower() or "desc"
        if direction not in directions:
            raise InvalidDelinquencyQuery(
                str((cfg.get("messages") or {}).get("invalidSortDir") or "Direção inválida.")
            )
        return (
            clamp_page(page, as_int(pagination.get("defaultPage"), 1)),
            clamp_page_size(
                page_size,
                default=as_int(pagination.get("defaultPageSize"), 20),
                maximum=as_int(pagination.get("maxPageSize"), 100),
            ),
            field,
            direction,
        )

    @staticmethod
    def _customer_scope(
        customer_code: str | None,
        store_code: str | None,
    ) -> tuple[str, str] | None:
        code = as_opt_str(customer_code)
        store = as_opt_str(store_code)
        if code and store:
            return code, store
        return None

    def _summary_for_customer(
        self,
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
        title_stats: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row, period_raw = self._find_customer_row(
            start,
            end,
            customer_code,
            store_code,
            refresh=refresh,
        )
        if row is None:
            return {
                "period": map_period(period_raw),
                "scopeNotice": self._customer_scope_notice(customer_code, store_code, ""),
                "totals": self._map_totals({}),
                "indicators": self._map_indicators({}),
            }

        mapped = self._map_customer(row)
        on_time_amount = max(mapped["totalAmount"] - mapped["lateAmount"], 0.0)
        stats = title_stats or self._collect_customer_title_stats(
            start,
            end,
            customer_code,
            store_code,
            refresh=refresh,
        )
        average_days_late = as_float(stats.get("averageDaysLate"))
        customer_label = mapped["shortName"] or mapped["customerName"] or customer_code
        return {
            "period": map_period(period_raw),
            "scopeNotice": self._customer_scope_notice(
                customer_code,
                store_code,
                customer_label,
            ),
            "totals": {
                "titles": mapped["totalTitles"],
                "onTimeTitles": mapped["onTimeTitles"],
                "lateTitles": mapped["lateTitles"],
                "totalAmount": mapped["totalAmount"],
                "onTimeAmount": on_time_amount,
                "lateAmount": mapped["lateAmount"],
            },
            "indicators": self._map_indicators(
                {
                    "percentual_em_dia_qtd": mapped["onTimePctByCount"],
                    "percentual_em_dia_valor": mapped["onTimePctByAmount"],
                    "percentual_inadimplencia_qtd": 100.0 - mapped["onTimePctByCount"],
                    "percentual_inadimplencia_valor": 100.0 - mapped["onTimePctByAmount"],
                    "media_dias_atraso": average_days_late,
                }
            ),
        }

    def _aging_for_customer(
        self,
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
        title_stats: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        template_payload = self._cached(
            "aging",
            {"start": start, "end": end},
            lambda: unwrap_data(
                self._gateway.fetch_delinquency_aging(start_date=start, end_date=end)
            ),
            refresh=refresh,
        )
        template_items = [
            item for item in template_payload.get("items") or [] if isinstance(item, dict)
        ]
        stats = title_stats or self._collect_customer_title_stats(
            start,
            end,
            customer_code,
            store_code,
            refresh=refresh,
        )
        totals_by_code = stats.get("buckets") if isinstance(stats.get("buckets"), dict) else {}
        period_raw = template_payload.get("periodo")
        total_count = sum(as_int(bucket.get("count")) for bucket in totals_by_code.values())
        total_amount = sum(as_float(bucket.get("amount")) for bucket in totals_by_code.values())
        items: list[dict[str, Any]] = []
        for template in template_items:
            code = as_str(template.get("codigo"))
            bucket = totals_by_code.get(code, {"count": 0, "amount": 0.0})
            count = as_int(bucket["count"])
            amount = as_float(bucket["amount"])
            count_pct = round(count * 100.0 / total_count, 2) if total_count > 0 else 0.0
            amount_pct = round(amount * 100.0 / total_amount, 2) if total_amount > 0 else 0.0
            items.append(
                self._map_aging(
                    {
                        "codigo": code,
                        "rotulo": template.get("rotulo"),
                        "ordem": template.get("ordem"),
                        "quantidade": count,
                        "valor": amount,
                        "percentual_quantidade": count_pct,
                        "percentual_valor": amount_pct,
                    }
                )
            )
        items.sort(key=lambda item: (as_int(item.get("order"), 99), item.get("code") or ""))
        return {"period": map_period(period_raw), "items": items}

    def _find_customer_row(
        self,
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
    ) -> tuple[dict[str, Any] | None, Any]:
        page = 1
        period_raw: Any = None
        page_size = as_int((_settings().get("pagination") or {}).get("maxPageSize"), 100)
        while True:
            payload = unwrap_data(
                self._gateway.fetch_delinquency_customers(
                    start_date=start,
                    end_date=end,
                    page=page,
                    page_size=page_size,
                    sort_by="customer_name",
                    sort_dir="asc",
                    search=customer_code,
                    only_with_delays=False,
                )
            )
            period_raw = payload.get("periodo")
            for item in payload.get("items") or []:
                if not isinstance(item, dict):
                    continue
                if (
                    as_str(item.get("cliente_codigo")) == customer_code
                    and as_str(item.get("loja")) == store_code
                ):
                    return item, period_raw
            pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
            if not pagination.get("has_next"):
                break
            page += 1
        return None, period_raw

    def _collect_customer_title_stats(
        self,
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((_settings().get("cacheTtlSeconds") or {}).get("titles"), 60)

        def loader() -> dict[str, Any]:
            totals_by_code: dict[str, dict[str, float | int]] = defaultdict(
                lambda: {"count": 0, "amount": 0.0}
            )
            late_days: list[int] = []
            for title in self._iter_customer_titles(
                start,
                end,
                customer_code,
                store_code,
                refresh=refresh,
            ):
                faixa = (
                    title.get("faixa_atraso")
                    if isinstance(title.get("faixa_atraso"), dict)
                    else {}
                )
                code = as_str(faixa.get("codigo"))
                if code:
                    totals_by_code[code]["count"] = as_int(totals_by_code[code]["count"]) + 1
                    totals_by_code[code]["amount"] = as_float(
                        totals_by_code[code]["amount"]
                    ) + as_float(title.get("valor_titulo"))
                days_late = as_int(title.get("dias_atraso"))
                if days_late > 0:
                    late_days.append(days_late)
            average_days_late = (
                round(sum(late_days) / len(late_days), 2) if late_days else 0.0
            )
            return {
                "buckets": {
                    code: {"count": as_int(bucket["count"]), "amount": as_float(bucket["amount"])}
                    for code, bucket in totals_by_code.items()
                },
                "averageDaysLate": average_days_late,
            }

        key = f"delinquency:customer-title-stats:{start}:{end}:{customer_code}:{store_code}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    def _top_delinquent_customers(
        self,
        user: object | None,
        *,
        start_date: str | None,
        end_date: str | None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        cfg = _settings().get("topDelinquentCustomers") or {}
        limit = clamp_page_size(
            as_int(cfg.get("limit"), 8),
            default=8,
            maximum=as_int((_settings().get("pagination") or {}).get("maxPageSize"), 100),
        )
        sort_by = as_str(cfg.get("sortBy")) or "on_time_by_quantity_percent"
        sort_dir = as_str(cfg.get("sortDir")) or "asc"
        only_with_delays = bool(cfg.get("onlyWithDelays", True))
        payload = self.customers(
            user,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=None,
            only_with_delays=only_with_delays,
            refresh=refresh,
        )
        return {
            "period": payload.get("period"),
            "items": self._filter_top_delinquent_items(payload.get("items") or []),
        }

    @staticmethod
    def _filter_top_delinquent_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            item
            for item in items
            if as_int(item.get("totalTitles")) > 0 and as_int(item.get("lateTitles")) > 0
        ]

    def _top_delinquent_from_items(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        filtered = self._filter_top_delinquent_items(items)
        filtered.sort(
            key=lambda item: (
                as_float(item.get("onTimePctByCount")),
                as_str(item.get("customerCode")),
                as_str(item.get("store")),
            )
        )
        return {"items": filtered}

    def _scope_customers_payload(
        self,
        customers: dict[str, Any],
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        items = [
            item
            for item in customers.get("items") or []
            if item.get("customerCode") == customer_code and item.get("store") == store_code
        ]
        if not items:
            row, _ = self._find_customer_row(
                start,
                end,
                customer_code,
                store_code,
                refresh=refresh,
            )
            if row:
                items = [self._map_customer(row)]
        pagination = customers.get("pagination") if isinstance(customers.get("pagination"), dict) else {}
        return {
            **customers,
            "items": items,
            "pagination": {
                **pagination,
                "page": 1,
                "totalItems": len(items),
                "totalPages": 1,
                "hasNext": False,
                "hasPrevious": False,
                "isComplete": True,
            },
        }

    def _iter_customer_titles(
        self,
        start: str | None,
        end: str | None,
        customer_code: str,
        store_code: str,
        *,
        refresh: bool,
    ):
        page = 1
        page_size = as_int((_settings().get("pagination") or {}).get("maxPageSize"), 100)
        while True:
            payload = unwrap_data(
                self._gateway.fetch_delinquency_titles(
                    start_date=start,
                    end_date=end,
                    customer_code=customer_code,
                    store_code=store_code,
                    status="all",
                    delay_range=None,
                    search=None,
                    page=page,
                    page_size=page_size,
                    sort_by="payment_date",
                    sort_dir="desc",
                )
            )
            items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
            yield from items
            pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
            if not pagination.get("has_next") or len(items) < page_size:
                break
            page += 1

    @staticmethod
    def _customer_scope_notice(customer_code: str, store_code: str, customer_label: str) -> str:
        template = str(_settings().get("customerScopeNotice") or "")
        label = customer_label.strip() or f"{customer_code}/{store_code}"
        return (
            template.replace("{customer}", label)
            .replace("{code}", customer_code)
            .replace("{store}", store_code)
        )

    @staticmethod
    def _map_totals(raw: Any) -> dict[str, Any]:
        source = raw if isinstance(raw, dict) else {}
        titles = source.get("titulos")
        if titles is None:
            titles = source.get("total_titulos")
        return {
            "titles": as_int(titles),
            "onTimeTitles": as_int(source.get("titulos_em_dia")),
            "lateTitles": as_int(source.get("titulos_atraso")),
            "totalAmount": as_float(source.get("valor_total")),
            "onTimeAmount": as_float(source.get("valor_em_dia")),
            "lateAmount": as_float(source.get("valor_atraso")),
        }

    @staticmethod
    def _map_indicators(raw: Any) -> dict[str, Any]:
        source = raw if isinstance(raw, dict) else {}
        on_time_count = as_float(source.get("percentual_em_dia_qtd"))
        on_time_amount = as_float(source.get("percentual_em_dia_valor"))
        late_count = source.get("percentual_atraso_qtd")
        if late_count is None:
            late_count = source.get("percentual_inadimplencia_qtd")
        late_amount = source.get("percentual_atraso_valor")
        if late_amount is None:
            late_amount = source.get("percentual_inadimplencia_valor")
        return {
            "onTimePctByCount": on_time_count,
            "onTimePctByAmount": on_time_amount,
            "latePctByCount": as_float(late_count, 100.0 - on_time_count),
            "latePctByAmount": as_float(late_amount, 100.0 - on_time_amount),
            "averageDaysLate": as_float(source.get("media_dias_atraso")),
        }

    @staticmethod
    def _map_month(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "month": as_str(item.get("mes")),
            "yearMonth": as_str(item.get("ano_mes")),
            "totalTitles": as_int(item.get("total_titulos")),
            "onTimeTitles": as_int(item.get("titulos_em_dia")),
            "lateTitles": as_int(item.get("titulos_atraso")),
            "totalAmount": as_float(item.get("valor_total")),
            "onTimeAmount": as_float(item.get("valor_em_dia")),
            "lateAmount": as_float(item.get("valor_atraso")),
            "onTimePctByCount": as_float(item.get("percentual_em_dia_qtd")),
            "onTimePctByAmount": as_float(item.get("percentual_em_dia_valor")),
        }

    @staticmethod
    def _map_aging(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": as_str(item.get("codigo")),
            "label": as_str(item.get("rotulo")),
            "order": as_int(item.get("ordem")),
            "count": as_int(item.get("quantidade")),
            "amount": as_float(item.get("valor")),
            "countPct": as_float(item.get("percentual_quantidade")),
            "amountPct": as_float(item.get("percentual_valor")),
        }

    @staticmethod
    def _map_customer(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "customerCode": as_str(item.get("cliente_codigo")),
            "store": as_str(item.get("loja")),
            "customerName": as_str(item.get("nome_cliente")),
            "shortName": as_str(item.get("nome_reduzido")),
            "totalTitles": as_int(item.get("total_titulos")),
            "onTimeTitles": as_int(item.get("titulos_em_dia")),
            "lateTitles": as_int(item.get("titulos_atraso")),
            "totalAmount": as_float(item.get("valor_total")),
            "lateAmount": as_float(item.get("valor_atraso")),
            "onTimePctByCount": as_float(item.get("percentual_em_dia_qtd")),
            "onTimePctByAmount": as_float(item.get("percentual_em_dia_valor")),
        }

    @staticmethod
    def _map_title(item: dict[str, Any]) -> dict[str, Any]:
        faixa = item.get("faixa_atraso") if isinstance(item.get("faixa_atraso"), dict) else {}
        return {
            "branch": as_str(item.get("filial")),
            "prefix": as_str(item.get("prefixo")),
            "number": as_str(item.get("numero")),
            "installment": as_str(item.get("parcela")),
            "type": as_str(item.get("tipo")),
            "customerCode": as_str(item.get("cliente_codigo")),
            "store": as_str(item.get("loja")),
            "customerName": as_str(item.get("nome_cliente")),
            "shortName": as_str(item.get("nome_reduzido")),
            "issueDate": as_opt_str(item.get("data_emissao")),
            "dueDate": as_opt_str(item.get("data_vencimento_real")),
            "paymentDate": as_opt_str(item.get("data_baixa")),
            "amount": as_float(item.get("valor_titulo")),
            "paidOnTime": bool(item.get("pago_em_dia")),
            "daysLate": as_int(item.get("dias_atraso")),
            "delayRange": {
                "code": as_str(faixa.get("codigo")),
                "label": as_str(faixa.get("rotulo")),
            },
        }
