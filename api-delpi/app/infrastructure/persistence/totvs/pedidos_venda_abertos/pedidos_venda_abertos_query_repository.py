from __future__ import annotations

from typing import Sequence

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

    def list_open_orders_for_customer(
        self,
        customer_code: str,
        customer_store: str,
    ) -> tuple[list[dict], dict]:
        """Pedidos em aberto de um par código/loja (Conta 360 — sem dump global)."""
        code = str(customer_code or "").strip()
        store = str(customer_store or "").strip()
        if not code or not store:
            return [], {
                "total_linhas": 0,
                "valor_total_aberto": 0,
                "saldo_total": 0,
                "itens_com_estoque": 0,
                "itens_estoque_parcial": 0,
                "itens_sem_estoque": 0,
            }

        customer_where = """
            WHERE NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), '') = ?
              AND NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '') = ?
        """
        params = (code, store)

        with self:
            summary_row = self.execute_one(
                f"""
                SELECT
                    COUNT(*) AS total_linhas,
                    ISNULL(SUM(v.valor_aberto), 0) AS valor_total_aberto,
                    ISNULL(SUM(v.saldo), 0) AS saldo_total,
                    SUM(CASE WHEN v.no_estoque >= v.saldo THEN 1 ELSE 0 END) AS itens_com_estoque,
                    SUM(
                        CASE WHEN v.no_estoque > 0 AND v.no_estoque < v.saldo THEN 1 ELSE 0 END
                    ) AS itens_estoque_parcial,
                    SUM(CASE WHEN v.no_estoque <= 0 THEN 1 ELSE 0 END) AS itens_sem_estoque
                {_ITEMS_FROM}
                {customer_where}
                """,
                params,
            )
            items = self.execute_query(
                f"""
                SELECT {_ITEMS_SELECT}
                {_ITEMS_FROM}
                {customer_where}
                ORDER BY v.data_entrega DESC
                """,
                params,
            )

        return items, summary_row or {}

    def aggregate_customer_open_order_metrics(
        self,
        customer_keys: Sequence[tuple[str, str]] | None = None,
    ) -> list[dict]:
        """Agrega valor aberto e atraso por (codigo_cadastro, loja_cadastro).

        Overdue = data_entrega < hoje e saldo > 0 (mesma regra do MFE commercial).
        """
        params: list = []
        filter_sql = ""
        if customer_keys:
            pairs = [
                (str(code or "").strip(), str(store or "").strip())
                for code, store in customer_keys
                if str(code or "").strip() and str(store or "").strip()
            ]
            if pairs:
                clauses = []
                for code, store in pairs:
                    clauses.append(
                        "("
                        "NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), '') = ? "
                        "AND NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '') = ?"
                        ")"
                    )
                    params.extend([code, store])
                filter_sql = "AND (" + " OR ".join(clauses) + ")"

        sql = f"""
            SELECT
                NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), '') AS customer_code,
                NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '') AS customer_store,
                MAX(NULLIF(LTRIM(RTRIM(v.nome_cliente)), '')) AS customer_name,
                ISNULL(SUM(v.valor_aberto), 0) AS open_value,
                CASE
                    WHEN SUM(
                        CASE
                            WHEN v.data_entrega IS NOT NULL
                             AND CAST(v.data_entrega AS date) < CAST(GETDATE() AS date)
                             AND ISNULL(v.saldo, 0) > 0
                            THEN 1
                            ELSE 0
                        END
                    ) > 0 THEN 1
                    ELSE 0
                END AS has_overdue
            {_ITEMS_FROM}
            WHERE NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), '') IS NOT NULL
              AND NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '') IS NOT NULL
              {filter_sql}
            GROUP BY
                NULLIF(LTRIM(RTRIM(C5.C5_CLIENTE)), ''),
                NULLIF(LTRIM(RTRIM(C5.C5_LOJACLI)), '')
            ORDER BY open_value DESC
        """
        with self:
            return self.execute_query(sql, tuple(params))
