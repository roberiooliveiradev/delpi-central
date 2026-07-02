from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DespesasCentroCustoResumoResponse:
    periodo: dict[str, str]
    total_periodo: float
    quantidade_lancamentos: int
    quantidade_centros_custo: int
    quantidade_fornecedores: int
    ticket_medio: float
    maior_lancamento: float

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "total_periodo": self.total_periodo,
            "quantidade_lancamentos": self.quantidade_lancamentos,
            "quantidade_centros_custo": self.quantidade_centros_custo,
            "quantidade_fornecedores": self.quantidade_fornecedores,
            "ticket_medio": self.ticket_medio,
            "maior_lancamento": self.maior_lancamento,
        }
