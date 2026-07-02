from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DespesasCentroCustoSeriePoint:
    ano_mes: str
    ano: int
    mes: int
    valor_total: float
    quantidade_lancamentos: int

    def to_dict(self) -> dict:
        return {
            "ano_mes": self.ano_mes,
            "ano": self.ano,
            "mes": self.mes,
            "valor_total": self.valor_total,
            "quantidade_lancamentos": self.quantidade_lancamentos,
        }


@dataclass
class DespesasCentroCustoSerieResponse:
    periodo: dict[str, str]
    serie: list[DespesasCentroCustoSeriePoint] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "serie": [point.to_dict() for point in self.serie],
        }
