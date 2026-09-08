from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Callable

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
    PurchaseRequestsGatewayError,
)
from app.infrastructure.gateways.strategic_indicators_gateway import (
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
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        allowed = self.authorization.allowed_units(user)
        if not allowed and not user.is_superadmin:
            raise AuthorizationError("Forbidden")

        start = start_date or _first_day_of_month()
        end = end_date or _today()
        period_label = f"{start} → {end}"

        if branch and branch not in {"", "all"}:
            self.authorization.require_unit(user, branch)
            branches = [branch]
            mode = "single"
        else:
            branches = allowed or ["01", "02"]
            mode = "consolidated" if len(branches) > 1 else "single"

        token = user.access_token or ""
        partial_failures: list[dict[str, str]] = []

        si_metrics: dict[str, dict[str, float | None]] = {}
        try:
            si_metrics = self.strategic_indicators.metrics_by_kpi(
                access_token=token,
                branch=branches[0] if mode == "single" else None,
                start_date=start,
                end_date=end,
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
                branches,
                lambda b: self.delpi_reads.get_otd(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("otd_percentage"),
                agg=_mean,
            ),
            "KPI-STOCK-VALUE": lambda: self._collect_numeric(
                branches,
                lambda b: self.delpi_reads.get_stock_value(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("total_stock_value"),
                agg=_sum,
            ),
            "KPI-TURNOVER": lambda: self._collect_numeric(
                branches,
                lambda b: self.delpi_reads.get_inventory_turnover(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("inventory_turnover_times"),
                agg=_mean,
            ),
            "KPI-CPV": lambda: self._collect_numeric(
                branches,
                lambda b: self.delpi_reads.get_cpv(
                    access_token=token,
                    branch=b,
                    start_date=start,
                    end_date=end,
                ).get("cpv_percentage"),
                agg=_mean,
            ),
            "KPI-SAVINGS": lambda: self._collect_numeric(
                branches,
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
                branches,
                lambda b: self.delpi_reads.get_safety_stock_summary(
                    access_token=token,
                    branch=b,
                ).get("below_safety_stock"),
                agg=_sum,
            ),
            "KPI-SC-OPEN": lambda: self._collect_sc_open(token, branches),
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
            meta_value = si_row.get("goal")
            idd_score = si_row.get("score")
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
                    "iddScore": idd_score,
                    "status": "available" if available else "unavailable",
                    "source": definition["source"],
                }
            )

        return {
            "scope": {"branches": branches, "mode": mode},
            "period": {"from": start, "to": end, "label": period_label},
            "kpis": kpis,
            "partialFailures": partial_failures,
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
