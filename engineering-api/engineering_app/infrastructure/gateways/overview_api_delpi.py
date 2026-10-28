"""Adapters da Visão geral — api-delpi Engineering + Strategic Indicators.

Contratos comprovados no G0 (doc 18):
- `GET /engineering/lmps/dashboard/summary` — owner LMP. Retorna
  `total_lmps`, `total_items?`, `percent_dentro_prazo`, `avg_lead_time`
  + campos de meta (`DashboardGoalFields`) enriquecidos pelo
  `enrich_dashboard_metric` (Strategic Indicators). Datas no formato
  `YYYYMMDD`; `branch` filtra unidade operacional.
- `GET /engineering/transforma-mais/processes/summary` — owner
  TRANSFORMA+. Retorna `implemented_solutions_count`,
  `total_gross_savings_in_period`, `average_roi` + mesmos campos de
  meta. Datas ISO; unidade via `filial_id`.
- `GET /dashboard/department-indicators?department_id=engineering` —
  Strategic Indicators (owner de IDD/score consolidado). Scores por
  `indicator_id` canônico.

AuthZ downstream: `ENGINEERING_LMP_ACCESS` / dashboard access via
`require_any_permission` — Bearer humano delegado; 403 → `forbidden`,
sem exposição de dado. Nenhuma regra de LMP/ROI/meta/IDD é derivada
aqui — somente mapeamento do payload oficial.
"""

from __future__ import annotations

import logging
from typing import Any

from engineering_app.application.models.overview import OverviewIndicator
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.overview_sources import (
    IndicatorFetch,
    OverviewQuery,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
    DownstreamError,
)

logger = logging.getLogger(__name__)

_SYSTEM = "api-delpi"

# indicator_id canônicos do Strategic Indicators (departamento
# engineering) — mesmos IDs declarados no dashboard de referência.
SI_IDD_BY_INDICATOR = {
    "lmp_on_time": "engineering-projects-on-time",
    "transforma_gross_savings": "engineering-transforma-plus",
}

_GOAL_FIELD_KEYS = (
    "has_goal",
    "goal_label",
    "goal_value",
    "comparable_goal",
    "reference_goal",
    "target",
    "goal_aggregation",
    "goal_mode",
    "goal_period_kind",
    "goal_period_partial",
    "goal_scope_branch",
    "goal_scope_label",
    "goal_scope_hint",
    "scope_type",
    "performance_direction",
    "value_unit",
    "value_prefix",
    "value_suffix",
    "value_decimals",
)


def _lmp_date(value: str | None) -> str | None:
    """YYYY-MM-DD → YYYYMMDD (contrato LMP); outros formatos passam."""
    if not value:
        return None
    stripped = value.strip()
    if len(stripped) == 10 and stripped[4] == "-" and stripped[7] == "-":
        return stripped.replace("-", "")
    return stripped


def _goal_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key) for key in _GOAL_FIELD_KEYS}


def _scope(query: OverviewQuery) -> str:
    return query.branch.strip() if query.branch and query.branch.strip() else "consolidado"


def _fetch_to_indicator_error(exc: Exception, *, family: str) -> IndicatorFetch:
    if isinstance(exc, DownstreamError) and exc.status_code in (401, 403):
        return IndicatorFetch(
            status="forbidden",
            message="Acesso negado pelo owner da fonte.",
        )
    if isinstance(exc, DownstreamError):
        return IndicatorFetch(
            status="unavailable",
            reason=exc.kind if exc.kind != "http" else "upstream_error",
        )
    logger.warning("overview_%s_unexpected_error", family, exc_info=True)
    return IndicatorFetch(status="unavailable", reason="upstream_error")


def _indicator(
    *,
    indicator_id: str,
    label: str,
    family: str,
    value: Any,
    unit: str,
    endpoint: str,
    payload: dict[str, Any],
    query: OverviewQuery,
) -> OverviewIndicator:
    return OverviewIndicator(
        id=indicator_id,
        label=label,
        family=family,
        availability="available",
        value=value if isinstance(value, (int, float)) else None,
        unit=unit,
        scope=_scope(query),
        start_date=query.start_date,
        end_date=query.end_date,
        source=_SYSTEM,
        source_endpoint=endpoint,
        **_goal_fields(payload),
    )


class ApiDelpiLmpOverviewSource:
    system = _SYSTEM
    endpoint = "GET /engineering/lmps/dashboard/summary"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> IndicatorFetch:
        try:
            data = await self._client.get(
                "/engineering/lmps/dashboard/summary",
                params={
                    "start_date": _lmp_date(query.start_date),
                    "end_date": _lmp_date(query.end_date),
                    "branch": query.branch,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception as exc:
            return _fetch_to_indicator_error(exc, family="lmp")

        if not isinstance(data, dict):
            return IndicatorFetch(status="unavailable", reason="contract_error")

        total = data.get("total_items", data.get("total_lmps"))
        if total in (None, 0):
            return IndicatorFetch(status="empty")

        indicators = (
            _indicator(
                indicator_id="lmp_on_time",
                label="% LMP dentro do prazo",
                family="lmp",
                value=data.get("percent_dentro_prazo"),
                unit="%",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
            _indicator(
                indicator_id="lmp_lead_time",
                label="Lead time médio",
                family="lmp",
                value=data.get("avg_lead_time"),
                unit="dias úteis",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
            _indicator(
                indicator_id="lmp_total_proposals",
                label="Total de propostas",
                family="lmp",
                value=total,
                unit="propostas",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
        )
        return IndicatorFetch(status="available", indicators=indicators)


class ApiDelpiTransformaOverviewSource:
    system = _SYSTEM
    endpoint = "GET /engineering/transforma-mais/processes/summary"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> IndicatorFetch:
        try:
            data = await self._client.get(
                "/engineering/transforma-mais/processes/summary",
                params={
                    "filial_id": query.branch,
                    "start_date": query.start_date,
                    "end_date": query.end_date,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception as exc:
            return _fetch_to_indicator_error(exc, family="transforma")

        if not isinstance(data, dict):
            return IndicatorFetch(status="unavailable", reason="contract_error")

        indicators = (
            _indicator(
                indicator_id="transforma_gross_savings",
                label="Ganhos brutos TRANSFORMA+",
                family="transforma",
                value=data.get("total_gross_savings_in_period"),
                unit="BRL",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
            _indicator(
                indicator_id="transforma_solutions",
                label="Soluções implementadas",
                family="transforma",
                value=data.get("implemented_solutions_count"),
                unit="soluções",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
            _indicator(
                indicator_id="transforma_roi",
                label="ROI médio TRANSFORMA+",
                family="transforma",
                value=data.get("average_roi"),
                unit="x",
                endpoint=self.endpoint,
                payload=data,
                query=query,
            ),
        )
        return IndicatorFetch(status="available", indicators=indicators)


class ApiDelpiEngineeringSiSource:
    """Scores IDD do departamento engineering (Strategic Indicators)."""

    system = _SYSTEM
    endpoint = "GET /dashboard/department-indicators"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def fetch_scores(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> dict[str, float] | None:
        try:
            data = await self._client.get(
                "/dashboard/department-indicators",
                params={
                    "department_id": "engineering",
                    "competence": query.competence,
                    "start_date": query.start_date,
                    "end_date": query.end_date,
                    "branch": query.branch,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
            )
        except Exception:
            logger.warning("overview_si_scores_unavailable", exc_info=True)
            return None

        if not isinstance(data, dict):
            return None
        item = data.get("item") if isinstance(data.get("item"), dict) else data
        rows = item.get("indicators") if isinstance(item, dict) else None
        if not isinstance(rows, list):
            return None

        scores: dict[str, float] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            indicator_id = row.get("indicator_id")
            score = row.get("score")
            if isinstance(indicator_id, str) and isinstance(score, (int, float)):
                scores[indicator_id] = float(score)
        return scores or None
