from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardEvolucaoRequest:
    view: str | None = None
    filial_id: str | None = None
    setor_id: str | None = None
    competencia_inicio: str | None = None
    competencia_fim: str | None = None
    granularity: str = "month"
