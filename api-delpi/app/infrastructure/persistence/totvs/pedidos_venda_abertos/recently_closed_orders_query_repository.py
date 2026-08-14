"""Recently closed sales-order lines (SC6 fully delivered in a lookback window)."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_DEFAULT_DAYS = 30
_MAX_DAYS = 90
_MAX_ROWS = 500


class RecentlyClosedOrdersQueryRepository(BaseRepository):
    """TOTVS-pure: lines with qty delivered covering sold qty in the last N days."""

    def list_recently_closed(self, *, days: int = _DEFAULT_DAYS) -> list[dict[str, Any]]:
        lookback = max(1, min(int(days or _DEFAULT_DAYS), _MAX_DAYS))
        sql = f"""
        SELECT TOP ({_MAX_ROWS})
            RTRIM(ISNULL(SA1.A1_NOME, '')) AS nome_cliente,
            'CLIENTE' AS tipo_entidade,
            RTRIM(ISNULL(C5.C5_TIPO, '')) AS tipo_pedido,
            RTRIM(ISNULL(C5.C5_PEDCLI, '')) AS pedido_cliente,
            RTRIM(C5.C5_FILIAL) AS filial,
            RTRIM(C5.C5_NUM) AS pedido,
            RTRIM(C6.C6_ITEM) AS linha,
            RTRIM(C6.C6_PRODUTO) AS produto,
            RTRIM(ISNULL(C6.C6_CLI, '')) AS codigo_cliente,
            RTRIM(ISNULL(C5.C5_CLIENTE, '')) AS codigo_cadastro,
            RTRIM(ISNULL(C5.C5_LOJACLI, '')) AS loja_cadastro,
            CAST(C6.C6_QTDVEN AS FLOAT) AS quantidade,
            CAST(C6.C6_QTDENT AS FLOAT) AS entregue,
            CAST(0 AS FLOAT) AS saldo,
            CONVERT(
                VARCHAR(10),
                TRY_CONVERT(DATE, NULLIF(RTRIM(C5.C5_EMISSAO), ''), 112),
                23
            ) AS data_despacho,
            CONVERT(
                VARCHAR(10),
                TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_ENTREG), ''), 112),
                23
            ) AS data_entrega,
            CAST(0 AS FLOAT) AS no_estoque,
            CAST(C6.C6_PRCVEN AS FLOAT) AS preco_venda,
            CAST(C6.C6_QTDENT * C6.C6_PRCVEN AS FLOAT) AS valor_aberto,
            'completed' AS kanbanStage
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
            ON C5.C5_FILIAL = C6.C6_FILIAL
           AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
           AND C5.D_E_L_E_T_ = ' '
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON SA1.A1_COD = C5.C5_CLIENTE
           AND SA1.A1_LOJA = C5.C5_LOJACLI
           AND SA1.D_E_L_E_T_ = ' '
        WHERE C6.D_E_L_E_T_ = ' '
          AND C5.C5_FILIAL IN ('01', '02')
          AND C6.C6_QTDENT > 0
          AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
          AND C5.C5_EMISSAO >= CONVERT(VARCHAR(8), DATEADD(DAY, -?, GETDATE()), 112)
        ORDER BY C5.C5_EMISSAO DESC, C5.C5_NUM DESC, C6.C6_ITEM
        """
        with self:
            return self.execute_query(sql, (lookback,))
