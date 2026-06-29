from __future__ import annotations

from app.domain.ports.pedidos_venda_abertos.pedidos_venda_abertos_query_repository_port import (
    PedidosVendaAbertosQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

VIEW = "dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES"

_ITEMS_SELECT = """
    v.nome_cliente,
    v.tipo_entidade,
    v.tipo_pedido,
    v.pedido_cliente,
    v.filial,
    v.pedido,
    v.linha,
    v.produto,
    v.codigo_cliente,
    NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), '') AS codigo_cadastro,
    NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '') AS loja_cadastro,
    v.quantidade,
    v.entregue,
    v.saldo,
    CONVERT(VARCHAR(10), v.data_despacho, 23) AS data_despacho,
    CONVERT(VARCHAR(10), v.data_entrega, 23) AS data_entrega,
    v.no_estoque,
    v.preco_venda,
    v.valor_aberto
"""

_ITEMS_FROM = f"""
    FROM {VIEW} v
    LEFT JOIN SC5010 C5 WITH (NOLOCK)
      ON C5.C5_FILIAL = v.filial
     AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(v.pedido))
     AND C5.D_E_L_E_T_ <> '*'
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
                FROM {VIEW} v
                """
            )
            items = self.execute_query(
                f"""
                SELECT {_ITEMS_SELECT}
                {_ITEMS_FROM}
                ORDER BY v.data_entrega DESC
                """
            )

        return items, summary_row or {}
