from __future__ import annotations

import logging
from typing import Any, Callable

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.parallel_block_runner import run_named_callables
from financial_app.application.services.payload_mapping import (
    as_float,
    as_int,
    as_opt_float,
    as_opt_str,
    as_str,
    unwrap_data,
)
from financial_app.application.services.response_cache import cached_fetch
from financial_app.core.security import FIN_ACCESS, FIN_EXPORT, can
from financial_app.domain.errors import FinancialError
from financial_app.domain.ports.financial_data_gateway import FinancialDataGateway
from financial_app.domain.services.branch_access_service import BranchAccessService
from financial_app.domain.services.period_range import (
    resolve_inclusive_period_or_default,
    rolling_month_series_bounds,
)

_LOGGER = logging.getLogger(__name__)


class InvalidBillingQuery(FinancialError):
    """Granularidade ou recorte fora do catálogo de faturamento."""


def _settings() -> dict[str, Any]:
    return load_content("billing.json")


class BillingService:
    def __init__(
        self,
        gateway: FinancialDataGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def dashboard(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        grain = self._resolve_granularity(granularity)
        workers = max(1, as_int(_settings().get("maxParallelBlocks"), 4))
        summary = self.summary(
            user,
            branch=branch,
            start_date=start,
            end_date=end,
            refresh=refresh,
        )
        extras = run_named_callables(
            {
                "series": lambda: self._safe_block(
                    lambda: self.series(
                        user,
                        start_date=start,
                        end_date=end,
                        granularity=grain,
                        refresh=refresh,
                    )
                ),
                "customers": lambda: self._safe_block(
                    lambda: self.customers(
                        user,
                        branch=branch,
                        start_date=start,
                        end_date=end,
                        refresh=refresh,
                    )
                ),
                "branches": lambda: self._safe_block(
                    lambda: self.branches(
                        user,
                        branch=branch,
                        start_date=start,
                        end_date=end,
                        refresh=refresh,
                    )
                ),
            },
            max_workers=workers,
        )
        return {
            "branch": scope,
            "period": {"startDate": start, "endDate": end},
            "granularity": grain,
            "summary": summary,
            "series": extras["series"],
            "customers": extras["customers"],
            "branches": extras["branches"],
        }

    def summary(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        payload = self._cached(
            "summary",
            {"branch": scope, "start": start, "end": end},
            lambda: unwrap_data(
                self._gateway.fetch_rol(branch=scope, start_date=start, end_date=end)
            ),
            refresh=refresh,
        )
        rol = as_float(payload.get("rol"))
        target = as_opt_float(payload.get("target") or payload.get("comparable_goal"))
        target_pct = as_opt_float(payload.get("rol_target_pct"))
        if target_pct is None and target and target > 0:
            target_pct = round((rol / target) * 100.0, 2)
        gap = None if target is None else round(rol - target, 2)
        return {
            "period": {"startDate": start, "endDate": end},
            "branch": scope,
            "rol": rol,
            "target": target,
            "targetPct": target_pct,
            "gap": gap,
            "goalLabel": as_opt_str(payload.get("goal_label")),
            "grossRevenue": as_float(payload.get("gross_revenue")),
            "otherValues": as_float(payload.get("other_values")),
            "itemsWithoutTes": as_float(payload.get("items_without_tes")),
            "returns": as_float(payload.get("returns")),
            "discounts": as_float(payload.get("discounts")),
            "icms": as_float(payload.get("icms")),
            "iss": as_float(payload.get("iss")),
            "pis": as_float(payload.get("pis")),
            "cofins": as_float(payload.get("cofins")),
            "ipiSeparated": as_float(payload.get("ipi_separated")),
            "taxes": as_float(payload.get("rol_taxes")),
            "financialTitles": as_float(payload.get("financial_titles")),
            "financialBalance": as_float(payload.get("financial_balance")),
            "composition": self._map_lines(payload, "composition"),
            "taxMix": self._map_lines(payload, "taxMix"),
            "detail": self._map_lines(payload, "detailLines"),
        }

    def series(
        self,
        user: object | None,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_use(user, FIN_ACCESS)
        grain = self._resolve_granularity(granularity)
        start, end = resolve_inclusive_period_or_default(start_date, end_date)
        if grain == "month":
            series_cfg = _settings().get("series") or {}
            series_months = as_int(series_cfg.get("months"), 12)
            start, end = rolling_month_series_bounds(
                start_date,
                end_date,
                months=series_months,
            )
        payload = self._cached(
            "series",
            {"start": start, "end": end, "grain": grain},
            lambda: unwrap_data(
                self._gateway.fetch_rol_series(
                    granularity=grain, start_date=start, end_date=end
                )
            ),
            refresh=refresh,
        )
        items = [
            {
                "period": as_str(item.get("periodo")),
                "sortKey": as_str(item.get("sort_key")),
                "startDate": as_str(item.get("start_date")),
                "endDate": as_str(item.get("end_date")),
                "rol01": as_float(item.get("rol_matrix")),
                "rol02": as_float(item.get("rol_branch")),
            }
            for item in payload.get("points") or []
            if isinstance(item, dict)
        ]
        return {
            "granularity": as_str(payload.get("granularity")) or grain,
            "truncated": bool(payload.get("truncated")),
            "items": items,
        }

    def customers(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        limit = max(1, as_int(_settings().get("customerLimit"), 12))
        payload = self._cached(
            "customers",
            {"branch": scope, "start": start, "end": end, "limit": limit},
            lambda: unwrap_data(
                self._gateway.fetch_rol_by_customer(
                    branch=scope,
                    start_date=start,
                    end_date=end,
                    limit=limit,
                    include_others=True,
                )
            ),
            refresh=refresh,
        )
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return {
            "branch": as_opt_str(payload.get("branch")) or scope,
            "items": [
                self._map_customer(item)
                for item in payload.get("items") or []
                if isinstance(item, dict)
            ],
            "others": self._map_customer(payload.get("others"))
            if isinstance(payload.get("others"), dict)
            else None,
            "totalRol": as_float(summary.get("total_rol")),
            "customersCount": as_int(summary.get("customers_count")),
        }

    def branches(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        payload = self._cached(
            "branches",
            {"start": start, "end": end},
            lambda: unwrap_data(
                self._gateway.fetch_rol_by_branch(start_date=start, end_date=end)
            ),
            refresh=refresh,
        )
        items = [
            {
                "branch": as_str(item.get("branch")),
                "rol": as_float(item.get("rol")),
                "grossRevenue": as_float(item.get("gross_revenue")),
                "returns": as_float(item.get("returns")),
                "discounts": as_float(item.get("discounts")),
            }
            for item in payload.get("items") or []
            if isinstance(item, dict)
        ]
        if scope in {"01", "02"}:
            items = [item for item in items if item["branch"] == scope]
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        total_rol = as_float(summary.get("total_rol"))
        if scope in {"01", "02"}:
            total_rol = sum(item["rol"] for item in items)
        return {
            "items": items,
            "totalRol": total_rol,
        }

    def invoices(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        if not can(user, FIN_EXPORT):
            raise PermissionError(str((_settings().get("messages") or {}).get("exportDenied") or ""))
        scope, start, end = self._prepare(user, branch, start_date, end_date)
        limit = max(1, as_int(_settings().get("invoiceLimit"), 8000))
        payload = unwrap_data(
            self._gateway.fetch_rol_invoices(
                branch=scope,
                start_date=start,
                end_date=end,
                limit=limit,
            )
        )
        kinds = _settings().get("invoiceKinds") or {}
        items = [
            self._map_invoice(item, kinds)
            for item in payload.get("items") or []
            if isinstance(item, dict)
        ]
        totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else {}
        return {
            "branch": scope,
            "period": {"startDate": start, "endDate": end},
            "truncated": bool(payload.get("truncated")),
            "items": items,
            "totals": {
                "count": as_int(totals.get("count"), len(items)),
                "gross": as_float(totals.get("gross")),
                "discounts": as_float(totals.get("discounts")),
                "returns": as_float(totals.get("returns")),
                "taxes": as_float(totals.get("taxes")),
                "rol": as_float(totals.get("rol")),
            },
        }

    def _prepare(
        self,
        user: object | None,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str | None, str, str]:
        self._branch_access.assert_can_use(user, FIN_ACCESS)
        scope = self._branch_access.resolve_branch_scope(user, branch)
        start, end = resolve_inclusive_period_or_default(start_date, end_date)
        return scope, start, end

    def _resolve_granularity(self, raw: str | None) -> str:
        allowed = {
            str(item).strip().lower()
            for item in (_settings().get("allowedGranularities") or [])
            if str(item).strip()
        }
        default = str(_settings().get("defaultGranularity") or "month").strip().lower()
        value = (raw or default).strip().lower()
        if value not in allowed:
            raise InvalidBillingQuery(str(_settings().get("messages", {}).get("invalidGranularity") or ""))
        return value

    def _cached(
        self,
        kind: str,
        parts: dict[str, Any],
        loader,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((_settings().get("cacheTtlSeconds") or {}).get(kind), 0)
        key = f"billing:{kind}:{sorted(parts.items())}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    def _safe_block(self, loader: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        try:
            payload = loader()
        except Exception as exc:
            messages = _settings().get("messages") or {}
            detail = str(exc)
            _LOGGER.warning("billing_block_failed detail=%s", detail)
            return {
                "available": False,
                "error": str(messages.get("blockFailed") or detail),
                "detail": detail,
            }
        payload["available"] = True
        payload["error"] = None
        return payload

    @staticmethod
    def _map_lines(payload: dict[str, Any], catalog_key: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in _settings().get(catalog_key) or []:
            if not isinstance(item, dict):
                continue
            source = as_str(item.get("source"))
            value = as_float(payload.get(source))
            rows.append(
                {
                    "key": as_str(item.get("key")),
                    "label": as_str(item.get("label")),
                    "value": value,
                    "role": as_str(item.get("role")) or None,
                }
            )
        return rows

    @staticmethod
    def _map_invoice(item: dict[str, Any], kinds: dict[str, Any]) -> dict[str, Any]:
        kind = as_str(item.get("kind")).strip().lower() or "sale"
        label = as_str(kinds.get(kind)) or kind
        return {
            "kind": kind,
            "kindLabel": label,
            "branch": as_str(item.get("branch")),
            "issueDate": as_str(item.get("issue_date")),
            "invoiceNumber": as_str(item.get("invoice_number")),
            "series": as_str(item.get("series")),
            "customerCode": as_str(item.get("customer_code")),
            "customerStore": as_str(item.get("customer_store")),
            "customerName": as_str(item.get("customer_name")),
            "gross": as_float(item.get("gross")),
            "discounts": as_float(item.get("discounts")),
            "returns": as_float(item.get("returns")),
            "taxes": as_float(item.get("taxes")),
            "rol": as_float(item.get("rol")),
        }

    @staticmethod
    def _map_customer(item: dict[str, Any] | None) -> dict[str, Any]:
        source = item or {}
        return {
            "customerCode": as_str(source.get("customer_code")),
            "customerStore": as_str(source.get("customer_store")),
            "customerName": as_str(source.get("customer_name")),
            "rol": as_float(source.get("rol")),
            "grossRevenue": as_float(source.get("gross_revenue")),
            "sharePct": as_opt_float(source.get("share_pct")),
            "rank": as_int(source.get("rank")),
        }
