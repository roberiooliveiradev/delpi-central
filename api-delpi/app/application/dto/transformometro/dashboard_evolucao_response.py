from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardEvolucaoItem:
    """Item bruto do Transformômetro-API (ainda com nomes internos `*_mes` / `competencia`)."""

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
        """Contrato público da fachada api-delpi (TV/chat) — independente de mês/dia.

        Upstream TM usa `competencia` e `investimento_total_mes`; a série segue a
        granularidade pedida, então a saída canônica é `periodo` + `investimento`.
        """
        payload: dict[str, Any] = {
            "periodo": str(self.competencia or ""),
            "economia_bruta": self.economia_bruta,
            "investimento": self.investimento_total_mes,
            "economia_liquida": self.economia_liquida_mes,
            "horas_economizadas": self.horas_economizadas_mes,
            "investimento_unico": self.investimento_unico_mes,
            "custo_recorrente": self.custo_recorrente_mes,
            "custo_recursos_compartilhados": self.custo_recursos_compartilhados_mes,
        }
        if self.ganho_capacidade is not None:
            payload["ganho_capacidade"] = self.ganho_capacidade
        if self.economia_reducao_volume is not None:
            payload["economia_reducao_volume"] = self.economia_reducao_volume
        return payload


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
