from __future__ import annotations

from app.domain.ports.pedidos_venda_abertos.ops_abertas_query_repository_port import (
    OpsAbertasQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

VIEW_DETALHE = "dbo.VW_OPS_ABERTAS_PRODUTO"
VIEW_RESUMO = "dbo.VW_OPS_ABERTAS_PRODUTO_RESUMO"

_DETALHE_SELECT = """
    filial,
    numero_op,
    produto,
    descricao_produto,
    tipo_produto,
    quantidade_op,
    quantidade_produzida,
    saldo_op,
    CONVERT(VARCHAR(10), data_emissao_op, 23) AS data_emissao_op,
    CONVERT(VARCHAR(10), data_inicio_prevista_op, 23) AS data_inicio_prevista_op,
    CONVERT(VARCHAR(10), data_fim_prevista_op, 23) AS data_fim_prevista_op,
    armazem,
    observacao_op
"""

_RESUMO_SELECT = """
    filial,
    produto,
    descricao_produto,
    tipo_produto,
    quantidade_ops_abertas,
    quantidade_total_ops,
    quantidade_total_produzida,
    saldo_total_ops,
    CONVERT(VARCHAR(10), primeira_data_prevista_op, 23) AS primeira_data_prevista_op,
    CONVERT(VARCHAR(10), ultima_data_prevista_op, 23) AS ultima_data_prevista_op
"""


class OpsAbertasQueryRepository(BaseRepository, OpsAbertasQueryRepositoryPort):

    def list_open_ops(self) -> tuple[list[dict], list[dict]]:
        with self:
            items = self.execute_query(
                f"""
                SELECT {_DETALHE_SELECT}
                FROM {VIEW_DETALHE}
                ORDER BY filial, produto, data_fim_prevista_op ASC
                """
            )
            summary_items = self._list_resumo_or_empty()

        return items, summary_items

    def _list_resumo_or_empty(self) -> list[dict]:
        try:
            return self.execute_query(
                f"""
                SELECT {_RESUMO_SELECT}
                FROM {VIEW_RESUMO}
                ORDER BY filial, produto
                """
            )
        except Exception as exc:
            if self._is_missing_view_error(exc):
                return []
            raise

    @staticmethod
    def _is_missing_view_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "invalid object name" in message and "vw_ops_abertas_produto_resumo" in message
