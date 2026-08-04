from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PedidosVendaAbertosSummary:
    total_linhas: int = 0
    valor_total_aberto: float = 0.0
    saldo_total: float = 0.0
    itens_com_estoque: int = 0
    itens_estoque_parcial: int = 0
    itens_sem_estoque: int = 0

    def to_dict(self) -> dict:
        return {
            "total_linhas": self.total_linhas,
            "valor_total_aberto": self.valor_total_aberto,
            "saldo_total": self.saldo_total,
            "itens_com_estoque": self.itens_com_estoque,
            "itens_estoque_parcial": self.itens_estoque_parcial,
            "itens_sem_estoque": self.itens_sem_estoque,
        }


@dataclass
class ListPedidosVendaAbertosResponse:
    items: list[dict]
    summary: PedidosVendaAbertosSummary
    portfolio_message: str | None = None
    portfolio_empty: bool = False
    portfolio_seller_id: str | None = None

    def to_dict(self) -> dict:
        payload = {
            "items": self.items,
            "summary": self.summary.to_dict(),
            "portfolio": {
                "empty": self.portfolio_empty,
                "message": self.portfolio_message,
                "seller_id": self.portfolio_seller_id,
            },
        }
        return payload
