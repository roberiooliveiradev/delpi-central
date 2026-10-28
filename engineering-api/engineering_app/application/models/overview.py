"""Contrato versionado da Visão geral do Portal Engenharia (F3.OVERVIEW).

Composição governada — a `engineering-api` normaliza os indicadores
oficiais dos owners (api-delpi/Strategic Indicators) sem recalcular
regras de LMP, ROI, metas ou IDD. Cada indicador carrega `source`,
`scope`, `period` e estado próprio; `goal_*`/`idd` só aparecem quando
o owner os fornece.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

OVERVIEW_SCHEMA_VERSION = "1.0"

# available: fonte respondeu com valor oficial.
# empty: fonte respondeu com sucesso e o owner reportou ausência legítima.
# unavailable: indisponível/timeout/transporte/contrato — nunca zero silencioso.
# forbidden: owner negou acesso ao recurso para o usuário autenticado.
IndicatorAvailability = Literal[
    "available",
    "empty",
    "unavailable",
    "forbidden",
]

# Status agregado: available (todas as famílias ok), partial (misto),
# unavailable (nenhuma utilizável).
OverviewStatus = Literal["available", "partial", "unavailable"]

IndicatorReason = Literal[
    "timeout",
    "transport_error",
    "upstream_error",
    "contract_error",
]

IndicatorFamily = Literal["lmp", "transforma"]


class OverviewFilters(BaseModel):
    """Filtros efetivos aplicados às fontes (eco do request validado)."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    competence: Optional[str] = None
    branch: Optional[str] = None


class OverviewIndicator(BaseModel):
    """Indicador oficial normalizado — valor e metadados do owner."""

    id: str
    label: str
    family: IndicatorFamily
    availability: IndicatorAvailability
    value: Optional[float] = None
    unit: Optional[str] = None
    scope: str = "consolidado"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: str
    source_endpoint: str
    # Campos de meta/IDD fornecidos pelo owner (Strategic Indicators via
    # api-delpi enrich_dashboard_metric) — repasse sem recálculo. O
    # conjunto espelha `DashboardGoalFields` do plugin-ui para que a
    # apresentação de meta/escopo/IDD siga a mesma regra do dashboard.
    has_goal: Optional[bool] = None
    goal_label: Optional[str] = None
    goal_value: Optional[float] = None
    comparable_goal: Optional[float] = None
    reference_goal: Optional[float] = None
    target: Optional[float] = None
    goal_aggregation: Optional[str] = None
    goal_mode: Optional[str] = None
    goal_period_kind: Optional[str] = None
    goal_period_partial: Optional[bool] = None
    goal_scope_branch: Optional[str] = None
    goal_scope_label: Optional[str] = None
    goal_scope_hint: Optional[str] = None
    scope_type: Optional[str] = None
    performance_direction: Optional[str] = None
    value_unit: Optional[str] = None
    value_prefix: Optional[str] = None
    value_suffix: Optional[str] = None
    value_decimals: Optional[int] = None
    idd: Optional[float] = None
    idd_label: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None


class OverviewResponse(BaseModel):
    schema_version: str = OVERVIEW_SCHEMA_VERSION
    generated_at: str
    filters: OverviewFilters
    status: OverviewStatus
    indicators: list[OverviewIndicator]
