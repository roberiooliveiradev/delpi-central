from __future__ import annotations

import logging
from typing import Any, Callable

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.cost_center_service import CostCenterService
from financial_app.application.services.delinquency_service import DelinquencyService
from financial_app.application.services.indicators_service import IndicatorsService
from financial_app.application.services.payload_mapping import (
    as_float,
    as_int,
    as_opt_float,
    unwrap_data,
)
from financial_app.domain.services.period_range import resolve_inclusive_period_or_default
from financial_app.core.security import (
    FIN_ACCESS,
    FIN_COST_CENTERS_VIEW,
    FIN_DELINQUENCY_VIEW,
    FIN_INDICATORS_VIEW,
    can,
)
from financial_app.domain.ports.financial_data_gateway import FinancialDataGateway
from financial_app.domain.services.branch_access_service import BranchAccessService

_LOGGER = logging.getLogger(__name__)


def _settings() -> dict[str, Any]:
    return load_content("overview.json")


class OverviewService:
    def __init__(
        self,
        gateway: FinancialDataGateway,
        *,
        delinquency: DelinquencyService,
        cost_centers: CostCenterService,
        indicators: IndicatorsService,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._delinquency = delinquency
        self._cost_centers = cost_centers
        self._indicators = indicators
        self._branch_access = branch_access or BranchAccessService()

    def build(
        self,
        user: object | None,
        *,
        branch: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        if not can(user, FIN_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal Financeiro.")
        scope = self._branch_access.resolve_branch_scope(user, branch)
        start, end = resolve_inclusive_period_or_default(start_date, end_date)

        kpi_cfg = _settings().get("kpis") or {}
        return {
            "branch": scope,
            "period": {"startDate": start, "endDate": end},
            "blocks": {
                "rol": self._kpi_block(
                    user,
                    label_key="rol",
                    cfg=kpi_cfg,
                    loader=lambda: unwrap_data(
                        self._gateway.fetch_rol(branch=scope, start_date=start, end_date=end)
                    ),
                    value_keys=("rol",),
                    amount_key=None,
                    extra=lambda data: {
                        "grossRevenue": as_opt_float(data.get("gross_revenue")),
                        "taxes": as_opt_float(data.get("rol_taxes")),
                    },
                ),
                "ebitda": self._kpi_block(
                    user,
                    label_key="ebitda",
                    cfg=kpi_cfg,
                    loader=lambda: unwrap_data(
                        self._gateway.fetch_ebitda_pct(
                            branch=scope, start_date=start, end_date=end
                        )
                    ),
                    value_keys=("ebitda_over_rol_pct",),
                    amount_key="ebitda_value",
                ),
                "fixedCost": self._kpi_block(
                    user,
                    label_key="fixedCost",
                    cfg=kpi_cfg,
                    loader=lambda: unwrap_data(
                        self._gateway.fetch_fixed_cost_pct(
                            branch=scope, start_date=start, end_date=end
                        )
                    ),
                    value_keys=("fixed_cost_over_rol_pct",),
                    amount_key="fixed_cost_value",
                ),
                "pmr": self._kpi_block(
                    user,
                    label_key="pmr",
                    cfg=kpi_cfg,
                    loader=lambda: unwrap_data(
                        self._gateway.fetch_pmr(branch=scope, start_date=start, end_date=end)
                    ),
                    value_keys=("pmr_days",),
                    amount_key=None,
                ),
                "delinquency": self._safe_block(
                    user,
                    FIN_DELINQUENCY_VIEW,
                    lambda: self._delinquency_block(user, start, end, refresh),
                ),
                "costCenters": self._safe_block(
                    user,
                    FIN_COST_CENTERS_VIEW,
                    lambda: self._cost_centers_block(user, scope, start, end, refresh),
                ),
                "indicators": self._safe_block(
                    user,
                    FIN_INDICATORS_VIEW,
                    lambda: self._indicators_block(user, scope, refresh),
                ),
            },
        }

    def _kpi_block(
        self,
        user: object | None,
        *,
        label_key: str,
        cfg: dict[str, Any],
        loader: Callable[[], dict[str, Any]],
        value_keys: tuple[str, ...],
        amount_key: str | None,
        extra: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        meta = cfg.get(label_key) if isinstance(cfg.get(label_key), dict) else {}
        try:
            data = loader()
        except Exception as exc:
            return self._failed(exc)
        value = None
        for key in value_keys:
            value = as_opt_float(data.get(key))
            if value is not None:
                break
        block: dict[str, Any] = {
            "available": True,
            "error": None,
            "label": meta.get("label"),
            "unit": meta.get("unit"),
            "value": value if value is not None else as_float(None),
            "target": as_opt_float(data.get("target")),
        }
        if amount_key:
            block["amount"] = as_opt_float(data.get(amount_key))
        if extra:
            block.update(extra(data))
        return block

    def _delinquency_block(
        self,
        user: object | None,
        start: str,
        end: str,
        refresh: bool,
    ) -> dict[str, Any]:
        summary = self._delinquency.summary(
            user, start_date=start, end_date=end, refresh=refresh
        )
        monthly = self._delinquency.monthly(
            user, start_date=start, end_date=end, refresh=refresh
        )
        return {
            "available": True,
            "error": None,
            "period": summary.get("period"),
            "scopeNotice": summary.get("scopeNotice"),
            "totals": summary.get("totals"),
            "indicators": summary.get("indicators"),
            "series": monthly.get("items") or [],
        }

    def _cost_centers_block(
        self,
        user: object | None,
        branch: str | None,
        start: str,
        end: str,
        refresh: bool,
    ) -> dict[str, Any]:
        limit = as_int(_settings().get("topCostCentersLimit"), 5)
        summary = self._cost_centers.summary(
            user,
            branch=branch,
            start_date=start,
            end_date=end,
            cost_center=None,
            supplier_code=None,
            supplier_store=None,
            refresh=refresh,
        )
        ranking = self._cost_centers.ranking_cost_centers(
            user,
            branch=branch,
            start_date=start,
            end_date=end,
            supplier_code=None,
            supplier_store=None,
            limit=limit,
            refresh=refresh,
        )
        return {
            "available": True,
            "error": None,
            "period": summary.get("period"),
            "totalAmount": summary.get("totalAmount"),
            "entryCount": summary.get("entryCount"),
            "costCenterCount": summary.get("costCenterCount"),
            "averageTicket": summary.get("averageTicket"),
            "top": ranking.get("items") or [],
        }

    def _indicators_block(
        self, user: object | None, branch: str | None, refresh: bool
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"refresh": refresh}
        if branch is not None:
            kwargs["branch"] = branch
        department = self._indicators.department(user, **kwargs)
        return {
            "available": True,
            "error": None,
            "department": department,
        }

    def _safe_block(
        self,
        user: object | None,
        permission: str,
        loader: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        messages = _settings().get("messages") or {}
        if not can(user, permission):
            return {
                "available": False,
                "error": str(messages.get("blockForbidden") or ""),
            }
        try:
            return loader()
        except PermissionError:
            return {
                "available": False,
                "error": str(messages.get("blockForbidden") or ""),
            }
        except Exception as exc:
            return self._failed(exc)

    @staticmethod
    def _failed(exc: Exception) -> dict[str, Any]:
        messages = _settings().get("messages") or {}
        detail = str(exc)
        _LOGGER.warning("overview_block_failed detail=%s", detail)
        return {
            "available": False,
            "error": _message_for_failure(detail, messages),
            "detail": detail,
        }


def _message_for_failure(detail: str, messages: dict[str, Any]) -> str:
    haystack = detail.lower()
    for matcher in _settings().get("errorMatchers") or []:
        if not isinstance(matcher, dict):
            continue
        needle = str(matcher.get("contains") or "").strip().lower()
        key = str(matcher.get("messageKey") or "").strip()
        if needle and key and needle in haystack:
            mapped = messages.get(key)
            if mapped:
                return str(mapped)
    return str(messages.get("blockFailed") or detail)
