from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DespesasCentroCustoRankingCentroItem:
    centro_custo_codigo: str
    centro_custo_descricao: str
    valor_total: float
    quantidade_lancamentos: int
    percentual: float

    def to_dict(self) -> dict:
        return {
            "centro_custo_codigo": self.centro_custo_codigo,
            "centro_custo_descricao": self.centro_custo_descricao,
            "valor_total": self.valor_total,
            "quantidade_lancamentos": self.quantidade_lancamentos,
            "percentual": self.percentual,
        }


@dataclass
class DespesasCentroCustoRankingCentrosResponse:
    periodo: dict[str, str]
    ranking: list[DespesasCentroCustoRankingCentroItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "ranking": [item.to_dict() for item in self.ranking],
        }
