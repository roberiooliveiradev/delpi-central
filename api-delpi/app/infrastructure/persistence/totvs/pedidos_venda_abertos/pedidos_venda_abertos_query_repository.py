from __future__ import annotations

from app.domain.ports.pedidos_venda_abertos.pedidos_venda_abertos_query_repository_port import (
    PedidosVendaAbertosQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

VIEW = "dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES"

_ITEMS_SELECT = """
    nome_cliente,
    tipo_entidade,
    tipo_pedido,
    pedido_cliente,
    filial,
    pedido,
    linha,
    produto,
    codigo_cliente,
    quantidade,
    entregue,
    saldo,
    CONVERT(VARCHAR(10), data_despacho, 23) AS data_despacho,
    CONVERT(VARCHAR(10), data_entrega, 23) AS data_entrega,
    no_estoque,
    preco_venda,
    valor_aberto
"""


class PedidosVendaAbertosQueryRepository(BaseRepository, PedidosVendaAbertosQueryRepositoryPort):

    def list_open_orders(self) -> tuple[list[dict], dict]:
        with self:
            summary_row = self.execute_one(
                f"""
                SELECT
                    COUNT(*) AS total_linhas,
                    ISNULL(SUM(valor_aberto), 0) AS valor_total_aberto,
                    ISNULL(SUM(saldo), 0) AS saldo_total,
                    SUM(CASE WHEN no_estoque >= saldo THEN 1 ELSE 0 END) AS itens_com_estoque,
                    SUM(
                        CASE WHEN no_estoque > 0 AND no_estoque < saldo THEN 1 ELSE 0 END
                    ) AS itens_estoque_parcial,
                    SUM(CASE WHEN no_estoque <= 0 THEN 1 ELSE 0 END) AS itens_sem_estoque
                FROM {VIEW}
                """
            )
            items = self.execute_query(
                f"""
                SELECT {_ITEMS_SELECT}
                FROM {VIEW}
                ORDER BY data_entrega DESC
                """
            )

        return items, summary_row or {}
