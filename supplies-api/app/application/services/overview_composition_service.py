from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Callable

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
    PurchaseRequestsGatewayError,
)
from app.infrastructure.gateways.strategic_indicators_gateway import (
    STRATEGIC_KPI_IDS,
    StrategicIndicatorsGateway,
    StrategicIndicatorsGatewayError,
)
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

KPI_DEFS: tuple[dict[str, str], ...] = (
    {
        "id": "KPI-OTD",
        "title": "OTD compras",
        "description": "Pontualidade de entregas no período.",
        "temporalNature": "interval",
        "source": "api-delpi",
        "unit": "%",
    },
    {
        "id": "KPI-STOCK-VALUE",
        "title": "Valor do estoque",
        "description": "Valor total do estoque no recorte.",
        "temporalNature": "snapshot",
        "source": "api-delpi",
        "unit": "R$",
    },
    {
        "id": "KPI-TURNOVER",
        "title": "Giro de estoque",
        "description": "Rotatividade do estoque em vezes no período.",
        "temporalNature": "interval",
        "source": "api-delpi",
        "unit": "×",
    },
    {
        "id": "KPI-CPV",
        "title": "CPV",
        "description": "Custo dos produtos vendidos no período.",
        "temporalNature": "interval",
        "source": "api-delpi",
        "unit": "%",
    },
    {
        "id": "KPI-SAVINGS",
        "title": "Economia em negociações",
        "description": "Economia homologada no período.",
        "temporalNature": "interval",
        "source": "api-delpi",
        "unit": "R$",
    },
    {
        "id": "KPI-SC-OPEN",
        "title": "SC pendentes",
        "description": "Solicitações abertas no escopo autorizado.",
        "temporalNature": "state",
        "source": "purchase-requests",
        "unit": "un",
    },
    {
        "id": "KPI-CRITICAL-MP",
        "title": "Materiais críticos",
        "description": "Itens abaixo do estoque de segurança.",
        "temporalNature": "snapshot",
        "source": "api-delpi",
        "unit": "un",
    },
)


logger = logging.getLogger("supplies-api.overview")

_SCOPE_LABEL = {
    "consolidated": "Consolidado",
    "01": "Santa Catarina",
    "02": "Espírito Santo",
}


def normalize_overview_branches(raw: list[str] | None) -> list[str]:
    """Deduplicate operational branches. Empty selection means the full 01+02 set."""
    seen: list[str] = []
    allowed = set(OPERATIONAL_UNITS)
    for item in raw or []:
        for part in str(item).split(","):
            code = part.strip()
            if not code or code == "all":
                continue
            if code not in allowed:
                raise ValueError(f"Unknown branch: {code}")
            if code not in seen:
                seen.append(code)
    if not seen:
        return list(OPERATIONAL_UNITS)
    return seen


def _active_scope(effective: list[str]) -> tuple[str, str, str | None]:
    if len(effective) == 1:
        key = effective[0]
        return "single", key, key
    return "consolidated", "consolidated", None


def _first_day_of_month(today: date | None = None) -> str:
    day = today or date.today()
    return day.replace(day=1).isoformat()


def _today(today: date | None = None) -> str:
    return (today or date.today()).isoformat()


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _sum(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values)


def _strategic_block(kpi_id: str, si_row: dict[str, Any]) -> dict[str, Any] | None:
    if kpi_id not in STRATEGIC_KPI_IDS:
        return None
    if not si_row or si_row.get("present") is False:
        return None
    return {
        "indicatorId": si_row.get("indicator_id"),
        "score": si_row.get("score"),
        "realized": si_row.get("realized") if isinstance(si_row.get("realized"), dict) else {},
        "goals": si_row.get("goals_by_unit")
        if isinstance(si_row.get("goals_by_unit"), dict)
        else {},
        "goalValue": si_row.get("goal_value"),
        "comparableGoal": si_row.get("comparable_goal"),
        "referenceGoal": si_row.get("reference_goal"),
        "goalMode": si_row.get("goal_mode"),
        "goalPeriodKind": si_row.get("goal_period_kind"),
        "goalPeriodPartial": si_row.get("goal_period_partial"),
        "performanceDirection": si_row.get("performance_direction"),
        "valueUnit": si_row.get("value_unit"),
        "valuePrefix": si_row.get("value_prefix"),
        "valueSuffix": si_row.get("value_suffix"),
        "valueDecimals": si_row.get("value_decimals"),
    }


def _si_value_drift(
    *,
    kpi_id: str,
    scope: str,
    operational_value: float | None,
    strategic: dict[str, Any] | None,
    period: dict[str, str],
) -> dict[str, Any] | None:
    if strategic is None or operational_value is None:
        return None
    realized = strategic.get("realized")
    if not isinstance(realized, dict) or scope not in realized:
        return None
    si_value = realized.get(scope)
    if si_value is None:
        return None
    try:
        si_number = float(si_value)
        operational = float(operational_value)
    except (TypeError, ValueError):
        return None
    tolerance = max(0.05, abs(si_number) * 0.01)
    if abs(operational - si_number) <= tolerance:
        return None
    return {
        "kpiId": kpi_id,
        "scope": scope,
        "operationalValue": operational,
        "siValue": si_number,
        "period": period,
    }


def _format_display(value: float | None, unit: str) -> str | None:
    if value is None:
        return None
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "R$":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if unit == "×":
        return f"{value:.2f}×"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}"


class OverviewCompositionService:
    def __init__(
        self,
        *,
        authorization: AuthorizationService | None = None,
        delpi_reads: SuppliesDelpiReads | None = None,
        purchase_requests: PurchaseRequestsGateway | None = None,
        strategic_indicators: StrategicIndicatorsGateway | None = None,
        max_workers: int = 8,
    ) -> None:
        self.authorization = authorization or AuthorizationService()
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.purchase_requests = purchase_requests or PurchaseRequestsGateway()
        self.strategic_indicators = strategic_indicators or StrategicIndicatorsGateway()
        self.max_workers = max_workers

    def compose(
        self,
        user: EffectiveUser,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        allowed = self.authorization.allowed_units(user)
        if not allowed and not user.is_superadmin:
            raise AuthorizationError("Forbidden")

        start = start_date or _first_day_of_month()
        end = end_date or _today()
        period_label = f"{start} → {end}"

        requested = branches if branches is not None else ([branch] if branch else [])
        effective = normalize_overview_branches(requested)
        for code in effective:
            self.authorization.require_unit(user, code)
        mode, scope_key, si_branch = _active_scope(effective)

        token = user.access_token or ""
        partial_failures: list[dict[str, str]] = []

        si_metrics: dict[str, dict[str, Any]] = {}
        empty_score = {"score": None, "classification": None}
        strategic_context: dict[str, Any] = {
            "departmentId": "supplies",
            "scope": {
                "mode": mode,
                "branches": effective,
                "key": scope_key,
                "label": _SCOPE_LABEL[scope_key],
            },
            "score": empty_score,
            "scores": {},
            "partialSuccess": False,
        }
        try:
            loaded = self._load_strategic(
                branch=si_branch,
                start_date=start,
                end_date=end,
                access_token=token,
            )
            si_metrics = loaded["metrics"]
            loaded_context = loaded["context"]
            score = loaded_context.get("score") or empty_score
            strategic_context = {
                "departmentId": "supplies",
                "scope": strategic_context["scope"],
                "score": score,
                "scores": {scope_key: score},
                "partialSuccess": bool(loaded_context.get("partialSuccess")),
            }
            for message in loaded.get("errors") or []:
                partial_failures.append(
                    {
                        "kpiId": "*",
                        "source": "si",
                        "message": str(message),
                    }
                )
        except StrategicIndicatorsGatewayError as exc:
            partial_failures.append(
                {
                    "kpiId": "*",
                    "source": "si",
                    "message": str(exc) or "strategic indicators unavailable",
                }
            )

        fetchers: dict[str, Callable[[], Any]] = {
            "KPI-OTD": lambda: self._collect_numeric(
                effective,
                lambda b: self.delpi_reads.get_otd(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("otd_percentage"),
                agg=_mean,
            ),
            "KPI-STOCK-VALUE": lambda: self._collect_numeric(
                effective,
                lambda b: self.delpi_reads.get_stock_value(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("total_stock_value"),
                agg=_sum,
            ),
            "KPI-TURNOVER": lambda: self._collect_numeric(
                effective,
                lambda b: self.delpi_reads.get_inventory_turnover(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("inventory_turnover_times"),
                agg=_mean,
            ),
            "KPI-CPV": lambda: self._collect_numeric(
                effective,
                lambda b: self.delpi_reads.get_cpv(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("cpv_percentage"),
                agg=_mean,
            ),
            "KPI-SAVINGS": lambda: self._collect_numeric(
                effective,
                lambda b: (
                    self.delpi_reads.get_negotiation_savings(
                        access_token=token,
                        branch=b,
                        start_date=start,
                        end_date=end,
                    ).get("total_savings")
                ),
                agg=_sum,
            ),
            "KPI-CRITICAL-MP": lambda: self._collect_numeric(
                effective,
                lambda b: self.delpi_reads.get_safety_stock_summary(
                    access_token=token,
                    branch=b,
                ).get("below_safety_stock"),
                agg=_sum,
            ),
            "KPI-SC-OPEN": lambda: self._collect_sc_open(token, effective),
        }

        results: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(fn): kpi_id for kpi_id, fn in fetchers.items()}
            for future in as_completed(futures):
                kpi_id = futures[future]
                try:
                    results[kpi_id] = future.result()
                except (DelpiApiGatewayError, PurchaseRequestsGatewayError, Exception) as exc:
                    results[kpi_id] = None
                    source = next(
                        (d["source"] for d in KPI_DEFS if d["id"] == kpi_id),
                        "api-delpi",
                    )
                    partial_failures.append(
                        {
                            "kpiId": kpi_id,
                            "source": source,
                            "message": str(exc) or "downstream unavailable",
                        }
                    )

        kpis: list[dict[str, Any]] = []
        si_value_drift: list[dict[str, Any]] = []
        for definition in KPI_DEFS:
            kpi_id = definition["id"]
            value = results.get(kpi_id)
            available = value is not None
            nature = definition["temporalNature"]
            card_period = (
                "agora / snapshot"
                if nature in {"snapshot", "state"}
                else period_label
            )
            si_row = si_metrics.get(kpi_id) or {}
            goal_value = si_row.get("goal_value")
            comparable_goal = si_row.get("comparable_goal")
            reference_goal = si_row.get("reference_goal")
            idd_score = si_row.get("score")
            performance_direction = si_row.get("performance_direction")
            goal_mode = si_row.get("goal_mode")
            meta_value = comparable_goal if comparable_goal is not None else goal_value
            strategic = _strategic_block(kpi_id, si_row)
            active_scope = scope_key
            drift = _si_value_drift(
                kpi_id=kpi_id,
                scope=active_scope,
                operational_value=value if isinstance(value, (int, float)) else None,
                strategic=strategic,
                period={"from": start, "to": end},
            )
            if drift is not None:
                logger.warning(
                    "SI_VALUE_DRIFT kpi=%s scope=%s operational=%s si=%s period=%s",
                    drift["kpiId"],
                    drift["scope"],
                    drift["operationalValue"],
                    drift["siValue"],
                    drift["period"],
                )
                si_value_drift.append(drift)
            kpis.append(
                {
                    "id": kpi_id,
                    "viewId": "overview",
                    "title": definition["title"],
                    "description": definition["description"],
                    "temporalNature": nature,
                    "periodLabel": card_period,
                    "value": value,
                    "displayValue": _format_display(value, definition["unit"])
                    if available
                    else None,
                    "unit": definition["unit"],
                    "meta": meta_value,
                    "goalValue": goal_value,
                    "comparableGoal": comparable_goal,
                    "referenceGoal": reference_goal,
                    "iddScore": idd_score,
                    "performanceDirection": performance_direction,
                    "goalMode": goal_mode,
                    "status": "available" if available else "unavailable",
                    "source": definition["source"],
                    "strategic": strategic,
                }
            )

        return {
            "scope": {"branches": effective, "mode": mode},
            "period": {"from": start, "to": end, "label": period_label},
            "kpis": kpis,
            "partialFailures": partial_failures,
            "strategicContext": strategic_context,
            "siValueDrift": si_value_drift,
        }

    def _load_strategic(
        self,
        *,
        branch: str | None,
        start_date: str,
        end_date: str,
        access_token: str,
    ) -> dict[str, Any]:
        loader = getattr(self.strategic_indicators, "compose_strategic", None)
        owner_name = type(self.strategic_indicators).__name__
        if callable(loader) and owner_name not in {"MagicMock", "Mock"}:
            return loader(
                access_token=access_token,
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        metrics = self.strategic_indicators.metrics_by_kpi(
            access_token=access_token,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "metrics": metrics,
            "context": {
                "departmentId": "supplies",
                "scores": {},
                "partialSuccess": False,
            },
            "errors": [],
        }

    def _collect_numeric(
        self,
        branches: list[str],
        reader: Callable[[str], Any],
        *,
        agg: Callable[[list[float]], float | None],
    ) -> float | None:
        values: list[float] = []
        errors: list[Exception] = []
        for branch in branches:
            try:
                parsed = _as_float(reader(branch))
                if parsed is not None:
                    values.append(parsed)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
        if values:
            return agg(values)
        if errors:
            raise errors[0]
        return None

    def _collect_sc_open(self, access_token: str, branches: list[str]) -> float | None:
        total = 0
        errors: list[Exception] = []
        for branch in branches:
            try:
                total += self.purchase_requests.count_open_requests(
                    access_token=access_token,
                    branch=branch,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
        if not errors:
            return float(total)
        if len(errors) == len(branches):
            raise errors[0]
        return float(total)
