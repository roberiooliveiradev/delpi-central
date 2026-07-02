from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DespesasCentroCustoRankingFornecedorItem:
    fornecedor_cliente_codigo: str
    loja: str
    razao_social: str
    valor_total: float
    quantidade_lancamentos: int
    percentual: float

    def to_dict(self) -> dict:
        return {
            "fornecedor_cliente_codigo": self.fornecedor_cliente_codigo,
            "loja": self.loja,
            "razao_social": self.razao_social,
            "valor_total": self.valor_total,
            "quantidade_lancamentos": self.quantidade_lancamentos,
            "percentual": self.percentual,
        }


@dataclass
class DespesasCentroCustoRankingFornecedoresResponse:
    periodo: dict[str, str]
    ranking: list[DespesasCentroCustoRankingFornecedorItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "ranking": [item.to_dict() for item in self.ranking],
        }
