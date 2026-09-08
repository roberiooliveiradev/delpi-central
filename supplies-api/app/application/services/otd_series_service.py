from __future__ import annotations

from datetime import date
from typing import Any

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
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


def _pick_otd_pct(point: dict[str, Any], *, branches: list[str], mode: str) -> float | None:
    f01 = _as_float(point.get("otd_filial_01"))
    f02 = _as_float(point.get("otd_filial_02"))
    if mode == "single" and branches:
        branch = branches[0]
        if branch == "01":
            return f01
        if branch == "02":
            return f02
    values = [value for value in (f01, f02) if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


class OtdSeriesService:
    """Compose OTD time series for Overview charts (api-delpi PO OTD series)."""

    def __init__(
        self,
        *,
        authorization: AuthorizationService | None = None,
        delpi_reads: SuppliesDelpiReads | None = None,
    ) -> None:
        self.authorization = authorization or AuthorizationService()
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()

    def compose(
        self,
        user: EffectiveUser,
        *,
        branch: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str = "month",
    ) -> dict[str, Any]:
        allowed = self.authorization.allowed_units(user)
        if not allowed and not user.is_superadmin:
            raise AuthorizationError("Forbidden")

        start = start_date or _first_day_of_month()
        end = end_date or _today()
        gran = (granularity or "month").strip().lower() or "month"
        if gran not in {"month", "week", "day"}:
            gran = "month"

        if branch and branch not in {"", "all"}:
            self.authorization.require_unit(user, branch)
            branches = [branch]
            mode = "single"
            delpi_branch: str | None = branch
        else:
            branches = allowed or ["01", "02"]
            mode = "consolidated" if len(branches) > 1 else "single"
            delpi_branch = branches[0] if mode == "single" else None

        partial_failures: list[dict[str, str]] = []
        points: list[dict[str, Any]] = []
        token = user.access_token or ""

        try:
            raw = self.delpi_reads.get_purchase_order_otd_series(
                access_token=token,
                branch=delpi_branch,
                start_date=start,
                end_date=end,
                granularity=gran,
            )
            for item in raw.get("points") or []:
                if not isinstance(item, dict):
                    continue
                period = str(item.get("periodo") or item.get("sort_key") or "").strip()
                if not period:
                    continue
                otd_pct = _pick_otd_pct(item, branches=branches, mode=mode)
                points.append(
                    {
                        "period": period,
                        "otdPct": otd_pct,
                        "onTime": None,
                        "total": None,
                    }
                )
        except DelpiApiGatewayError as exc:
            partial_failures.append(
                {
                    "source": "api-delpi",
                    "message": str(exc) or "otd series unavailable",
                }
            )

        return {
            "scope": {"branches": branches, "mode": mode},
            "period": {"from": start, "to": end, "label": f"{start} → {end}"},
            "granularity": gran,
            "points": points,
            "partialFailures": partial_failures,
        }
