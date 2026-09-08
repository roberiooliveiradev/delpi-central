from __future__ import annotations

from datetime import date
from typing import Any

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.strategic_indicators_gateway import (
    StrategicIndicatorsGateway,
    StrategicIndicatorsGatewayError,
)
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads


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


class OtdAggregateService:
    """Compose OTD aggregate for analytics gauges (api-delpi OTD + SI meta)."""

    def __init__(
        self,
        *,
        authorization: AuthorizationService | None = None,
        delpi_reads: SuppliesDelpiReads | None = None,
        strategic_indicators: StrategicIndicatorsGateway | None = None,
    ) -> None:
        self.authorization = authorization or AuthorizationService()
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.strategic_indicators = strategic_indicators or StrategicIndicatorsGateway()

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

        if branch and branch not in {"", "all"}:
            self.authorization.require_unit(user, branch)
            branches = [branch]
            mode = "single"
        else:
            branches = allowed or ["01", "02"]
            mode = "consolidated" if len(branches) > 1 else "single"

        token = user.access_token or ""
        partial_failures: list[dict[str, str]] = []
        by_branch: dict[str, dict[str, float | None]] = {}
        otd_values: list[float] = []

        goal: float | None = None
        try:
            goals = self.strategic_indicators.goals_by_kpi(
                access_token=token,
                branch=branches[0] if mode == "single" else None,
                start_date=start,
                end_date=end,
            )
            goal = goals.get("KPI-OTD")
        except StrategicIndicatorsGatewayError as exc:
            partial_failures.append(
                {
                    "source": "si",
                    "message": str(exc) or "strategic indicators unavailable",
                }
            )

        for unit in branches:
            try:
                summary = self.delpi_reads.get_otd(
                    access_token=token,
                    branch=unit,
                    start_date=start,
                    end_date=end,
                )
                otd_pct = _as_float(summary.get("otd_percentage"))
                on_time = _as_float(summary.get("on_time_count") or summary.get("onTime"))
                total = _as_float(summary.get("total_count") or summary.get("total"))
                by_branch[unit] = {
                    "otdPct": otd_pct,
                    "goal": goal,
                    "onTime": on_time,
                    "total": total,
                }
                if otd_pct is not None:
                    otd_values.append(otd_pct)
            except DelpiApiGatewayError as exc:
                by_branch[unit] = {
                    "otdPct": None,
                    "goal": goal,
                    "onTime": None,
                    "total": None,
                }
                partial_failures.append(
                    {
                        "source": "api-delpi",
                        "branch": unit,
                        "message": str(exc) or "otd unavailable",
                    }
                )

        aggregate_on_time = None
        aggregate_total = None
        if mode == "single" and branches:
            entry = by_branch.get(branches[0]) or {}
            aggregate_on_time = entry.get("onTime")
            aggregate_total = entry.get("total")

        return {
            "scope": {"branches": branches, "mode": mode},
            "period": {"from": start, "to": end, "label": f"{start} → {end}"},
            "otdPct": _mean(otd_values),
            "goal": goal,
            "onTime": aggregate_on_time,
            "total": aggregate_total,
            "byBranch": by_branch,
            "partialFailures": partial_failures,
        }
