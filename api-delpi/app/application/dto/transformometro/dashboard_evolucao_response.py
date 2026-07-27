from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardEvolucaoItem:
    competencia: str
    economia_bruta: float
    investimento_unico_mes: float
    custo_recorrente_mes: float
    custo_recursos_compartilhados_mes: float
    investimento_total_mes: float
    economia_liquida_mes: float
    horas_economizadas_mes: float
    ganho_capacidade: float | None = None
    economia_reducao_volume: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class DashboardEvolucaoResponse:
    total: int
    items: list[DashboardEvolucaoItem]
    granularity: str

    def to_dict(self) -> dict[str, Any]:
        """Envelope alinhado às séries de produção (`points`, não `items`)."""
        return {
            "granularity": self.granularity,
            "total": self.total,
            "points": [item.to_dict() for item in self.items],
        }
