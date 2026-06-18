from __future__ import annotations

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
    InspecoesEntradaHistoricoFilters,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

RESUMO_VIEW = "dbo.vw_minha_delpi_inspecoes_entrada_resumo_filial"
PENDENTES_VIEW = "dbo.vw_minha_delpi_inspecoes_entrada_pendentes"
PENDENTES_FORNECEDOR_VIEW = "dbo.vw_minha_delpi_inspecoes_entrada_pendentes_fornecedor"
REJEITADAS_ENSAIADOR_VIEW = "dbo.vw_minha_delpi_inspecoes_entrada_rejeitadas_ensaiador"
HISTORICO_VIEW = "dbo.vw_minha_delpi_inspecoes_entrada_historico_tela"

_RESUMO_SELECT = """
    Filial,
    Inspecoes_Pendentes,
    Ja_Inspecionados,
    Inspecoes_Aprovadas,
    Inspecoes_Rejeitadas,
    Taxa_Aprovacao,
    Qtde_Inspecoes_Com_Tempo,
    Tempo_Medio_Horas,
    Tempo_Medio_Dias
"""

_PENDENTES_SELECT = """
    Filial,
    Data_Recebimento,
    Hora_Recebimento,
    Nota_Fiscal,
    Codigo_Fornecedor,
    Loja_Fornecedor,
    Nome_Fornecedor,
    Codigo_Produto,
    Quantidade,
    Unidade_Medida,
    Codigo_Situacao,
    Status_Inspecao
"""

_PENDENTES_ORDER_BY = """
    ORDER BY Data_Recebimento ASC, Hora_Recebimento ASC, Nota_Fiscal ASC
"""

_PENDENTES_FORNECEDOR_SELECT = """
    Filial,
    Nome_Fornecedor,
    Qtde_Pendentes
"""

_PENDENTES_FORNECEDOR_ORDER_BY = """
    ORDER BY Qtde_Pendentes DESC, Nome_Fornecedor ASC
"""

_REJEITADAS_ENSAIADOR_SELECT = """
    Filial,
    Matricula_Ensaiador,
    Nome_Ensaiador,
    Login_Ensaiador,
    Qtde_Inspecoes_Rejeitadas
"""

_REJEITADAS_ENSAIADOR_ORDER_BY = """
    ORDER BY Qtde_Inspecoes_Rejeitadas DESC, Nome_Ensaiador ASC
"""

_REJEITADAS_PRODUTO_SELECT = """
    Filial,
    Id_Inspecao,
    Data_Laudo,
    Hora_Laudo,
    Nota_Fiscal,
    Nome_Fornecedor,
    Codigo_Produto,
    Lote,
    Quantidade,
    Unidade_Medida
"""

_REJEITADAS_PRODUTO_ORDER_BY = """
    ORDER BY Data_Laudo DESC, Hora_Laudo DESC, Nota_Fiscal DESC
"""

_SB1_DESCRICAO_APPLY = """
OUTER APPLY (
    SELECT TOP 1
        LTRIM(RTRIM(SB1_INNER.B1_DESC)) AS B1_DESC
    FROM dbo.SB1010 SB1_INNER
    WHERE SB1_INNER.D_E_L_E_T_ = ''
      AND LTRIM(RTRIM(SB1_INNER.B1_COD)) = LTRIM(RTRIM(src.Codigo_Produto))
      AND (
            LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = ''
            OR LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial))
      )
    ORDER BY
        CASE
            WHEN LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial)) THEN 0
            ELSE 1
        END
) SB1
"""

_HISTORICO_SELECT = """
    Filial,
    Id_Inspecao,
    Data_Recebimento,
    Hora_Recebimento,
    Data_Laudo,
    Hora_Laudo,
    Nota_Fiscal,
    Serie_Nota_Fiscal,
    Item_Nota_Fiscal,
    Codigo_Fornecedor,
    Loja_Fornecedor,
    Nome_Fornecedor,
    Codigo_Produto,
    Lote,
    Lote_Fornecedor,
    Quantidade,
    Unidade_Medida,
    Codigo_Situacao,
    Status_Inspecao,
    Resultado_Resumo,
    Codigo_Laudo,
    Quantidade_Aprovada,
    Quantidade_Rejeitada,
    Justificativa_Laudo,
    Matricula_Ensaiador,
    Nome_Ensaiador,
    Login_Ensaiador,
    Qtde_Ensaios,
    Qtde_Ensaios_Reprovados,
    Eh_Aprovada,
    Eh_Rejeitada
"""

_HISTORICO_ORDER_BY = """
    ORDER BY
        Data_Laudo DESC,
        Hora_Laudo DESC,
        Nota_Fiscal DESC,
        Item_Nota_Fiscal ASC
"""


def _build_historico_where(
    branch: str,
    filters: InspecoesEntradaHistoricoFilters,
) -> tuple[str, list]:
    clauses = ["Filial = ?"]
    params: list = [branch]

    if filters.result:
        clauses.append("Resultado_Resumo = ?")
        params.append(filters.result)
    if filters.date_from:
        clauses.append("Data_Laudo >= ?")
        params.append(filters.date_from)
    if filters.date_to:
        clauses.append("Data_Laudo <= ?")
        params.append(filters.date_to)
    if filters.supplier:
        clauses.append("Nome_Fornecedor COLLATE Latin1_General_CI_AI LIKE ?")
        params.append(f"%{filters.supplier}%")
    if filters.product_code:
        clauses.append("UPPER(LTRIM(RTRIM(Codigo_Produto))) = UPPER(?)")
        params.append(filters.product_code)
    if filters.inspector:
        clauses.append("Nome_Ensaiador COLLATE Latin1_General_CI_AI LIKE ?")
        params.append(f"%{filters.inspector}%")
    if filters.invoice_number:
        clauses.append("UPPER(LTRIM(RTRIM(Nota_Fiscal))) = UPPER(?)")
        params.append(filters.invoice_number)
    if filters.lot:
        clauses.append("UPPER(LTRIM(RTRIM(Lote))) = UPPER(?)")
        params.append(filters.lot)

    return " AND ".join(clauses), params


class InspecoesEntradaRepository(BaseRepository, InspecoesEntradaRepositoryPort):
    def get_resumo_by_branch(self, branch: str) -> dict | None:
        with self:
            return self.execute_one(
                f"""
                SELECT {_RESUMO_SELECT}
                FROM {RESUMO_VIEW}
                WHERE Filial = ?
                """,
                (branch,),
            )

    def count_pendentes_by_branch(self, branch: str) -> int:
        with self:
            row = self.execute_one(
                f"""
                SELECT COUNT(*) AS total
                FROM {PENDENTES_VIEW}
                WHERE Filial = ?
                """,
                (branch,),
            )
        return int((row or {}).get("total") or 0)

    def list_pendentes_by_branch(
        self,
        branch: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]:
        offset = (max(page, 1) - 1) * page_size
        with self:
            return self.execute_query(
                f"""
                SELECT src.*,
                       NULLIF(LTRIM(RTRIM(SB1.B1_DESC)), '') AS Descricao_Produto
                FROM (
                    SELECT {_PENDENTES_SELECT}
                    FROM {PENDENTES_VIEW}
                    WHERE Filial = ?
                    {_PENDENTES_ORDER_BY}
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                ) src
                OUTER APPLY (
                    SELECT TOP 1
                        LTRIM(RTRIM(SB1_INNER.B1_DESC)) AS B1_DESC
                    FROM dbo.SB1010 SB1_INNER
                    WHERE SB1_INNER.D_E_L_E_T_ = ''
                      AND LTRIM(RTRIM(SB1_INNER.B1_COD)) = LTRIM(RTRIM(src.Codigo_Produto))
                      AND (
                            LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = ''
                            OR LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial))
                      )
                    ORDER BY
                        CASE
                            WHEN LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial)) THEN 0
                            ELSE 1
                        END
                ) SB1
                """,
                (branch, offset, page_size),
            )

    def list_pendentes_fornecedor_by_branch(self, branch: str) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_PENDENTES_FORNECEDOR_SELECT}
                FROM {PENDENTES_FORNECEDOR_VIEW}
                WHERE Filial = ?
                {_PENDENTES_FORNECEDOR_ORDER_BY}
                """,
                (branch,),
            )

    def list_rejeitadas_ensaiador_by_branch(self, branch: str) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_REJEITADAS_ENSAIADOR_SELECT}
                FROM {REJEITADAS_ENSAIADOR_VIEW}
                WHERE Filial = ?
                {_REJEITADAS_ENSAIADOR_ORDER_BY}
                """,
                (branch,),
            )

    def count_rejeitadas_by_branch(self, branch: str) -> int:
        with self:
            row = self.execute_one(
                f"""
                SELECT COUNT(*) AS total
                FROM {HISTORICO_VIEW}
                WHERE Filial = ?
                  AND Resultado_Resumo = 'REJEITADA'
                """,
                (branch,),
            )
        return int((row or {}).get("total") or 0)

    def list_rejeitadas_by_branch(self, branch: str, *, limit: int) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT src.*,
                       NULLIF(LTRIM(RTRIM(SB1.B1_DESC)), '') AS Descricao_Produto
                FROM (
                    SELECT {_REJEITADAS_PRODUTO_SELECT}
                    FROM {HISTORICO_VIEW}
                    WHERE Filial = ?
                      AND Resultado_Resumo = 'REJEITADA'
                    {_REJEITADAS_PRODUTO_ORDER_BY}
                    OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                ) src
                {_SB1_DESCRICAO_APPLY}
                """,
                (branch, limit),
            )

    def count_historico_by_branch(
        self,
        branch: str,
        filters: InspecoesEntradaHistoricoFilters,
    ) -> int:
        where_clause, params = _build_historico_where(branch, filters)
        with self:
            row = self.execute_one(
                f"""
                SELECT COUNT(*) AS total
                FROM {HISTORICO_VIEW}
                WHERE {where_clause}
                """,
                tuple(params),
            )
        return int((row or {}).get("total") or 0)

    def list_historico_by_branch(
        self,
        branch: str,
        *,
        page: int,
        page_size: int,
        filters: InspecoesEntradaHistoricoFilters,
    ) -> list[dict]:
        where_clause, params = _build_historico_where(branch, filters)
        offset = (max(page, 1) - 1) * page_size
        query_params = tuple(params + [offset, page_size])
        with self:
            return self.execute_query(
                f"""
                SELECT {_HISTORICO_SELECT}
                FROM {HISTORICO_VIEW}
                WHERE {where_clause}
                {_HISTORICO_ORDER_BY}
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """,
                query_params,
            )

    def get_historico_header_by_inspection_id(
        self,
        branch: str,
        inspection_id: str,
    ) -> dict | None:
        with self:
            return self.execute_one(
                f"""
                SELECT src.*,
                       NULLIF(LTRIM(RTRIM(SB1.B1_DESC)), '') AS Descricao_Produto
                FROM (
                    SELECT {_HISTORICO_SELECT}
                    FROM {HISTORICO_VIEW}
                    WHERE Filial = ?
                      AND Id_Inspecao = ?
                ) src
                OUTER APPLY (
                    SELECT TOP 1
                        LTRIM(RTRIM(SB1_INNER.B1_DESC)) AS B1_DESC
                    FROM dbo.SB1010 SB1_INNER
                    WHERE SB1_INNER.D_E_L_E_T_ = ''
                      AND LTRIM(RTRIM(SB1_INNER.B1_COD)) = LTRIM(RTRIM(src.Codigo_Produto))
                      AND (
                            LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = ''
                            OR LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial))
                      )
                    ORDER BY
                        CASE
                            WHEN LTRIM(RTRIM(SB1_INNER.B1_FILIAL)) = LTRIM(RTRIM(src.Filial)) THEN 0
                            ELSE 1
                        END
                ) SB1
                """,
                (branch, inspection_id),
            )

    def list_tests_by_inspection_header(
        self,
        branch: str,
        header: dict,
    ) -> list[dict]:
        with self:
            return self.execute_query(
                """
                SELECT
                    LTRIM(RTRIM(QER.QER_ENSAIO)) AS Codigo_Ensaio,
                    LTRIM(RTRIM(QE1.QE1_DESCPO)) AS Nome_Ensaio,
                    NULLIF(LTRIM(RTRIM(QE8.QE8_TEXTO)), '') AS Especificacao_Textual,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_NOMINA)), '') AS Valor_Nominal,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_LIE)), '') AS Limite_Inferior_Espec,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_LSE)), '') AS Limite_Superior_Espec,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_LIC)), '') AS Limite_Inferior_Controle,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_LSC)), '') AS Limite_Superior_Controle,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_MINMAX)), '') AS Regra_Min_Max,
                    NULLIF(LTRIM(RTRIM(QE7.QE7_UNIMED)), '') AS Unidade_Especificacao,
                    NULLIF(LTRIM(RTRIM(QEQ.QEQ_MEDICA)), '') AS Medicao_Textual,
                    NULLIF(LTRIM(RTRIM(QES.QES_MEDICA)), '') AS Medicao_Numerica,
                    NULLIF(LTRIM(RTRIM(QES.QES_INDMED)), '') AS Indicador_Medicao_Numerica,
                    CASE
                        WHEN NULLIF(LTRIM(RTRIM(QES.QES_MEDICA)), '') IS NOT NULL THEN 'QES'
                        WHEN NULLIF(LTRIM(RTRIM(QEQ.QEQ_MEDICA)), '') IS NOT NULL THEN 'QEQ'
                        ELSE NULL
                    END AS Fonte_Medicao,
                    COALESCE(
                        NULLIF(LTRIM(RTRIM(QES.QES_MEDICA)), ''),
                        NULLIF(LTRIM(RTRIM(QEQ.QEQ_MEDICA)), '')
                    ) AS Valor_Medido,
                    COALESCE(
                        NULLIF(LTRIM(RTRIM(QE8.QE8_TEXTO)), ''),
                        CASE
                            WHEN NULLIF(LTRIM(RTRIM(QE7.QE7_NOMINA)), '') IS NOT NULL
                              OR NULLIF(LTRIM(RTRIM(QE7.QE7_LIE)), '') IS NOT NULL
                              OR NULLIF(LTRIM(RTRIM(QE7.QE7_LSE)), '') IS NOT NULL
                            THEN CONCAT(
                                'Nominal: ',
                                COALESCE(NULLIF(LTRIM(RTRIM(QE7.QE7_NOMINA)), ''), '-'),
                                ' | Min: ',
                                COALESCE(NULLIF(LTRIM(RTRIM(QE7.QE7_LIE)), ''), '-'),
                                ' | Max: ',
                                COALESCE(NULLIF(LTRIM(RTRIM(QE7.QE7_LSE)), ''), '-'),
                                CASE
                                    WHEN NULLIF(LTRIM(RTRIM(QE7.QE7_UNIMED)), '') IS NOT NULL
                                    THEN CONCAT(' ', LTRIM(RTRIM(QE7.QE7_UNIMED)))
                                    ELSE ''
                                END
                            )
                            ELSE NULL
                        END
                    ) AS Especificacao_Esperada,
                    LTRIM(RTRIM(QER.QER_RESULT)) AS Codigo_Resultado,
                    QER.QER_DTMEDI AS Data_Medicao,
                    QER.QER_HRMEDI AS Hora_Medicao,
                    QER.QER_AMOSTR AS Numero_Amostra,
                    LTRIM(RTRIM(QER.QER_CHAVE)) AS Chave_Qer,
                    LTRIM(RTRIM(QER.QER_NUMSEQ)) AS Numero_Sequencia,
                    LTRIM(RTRIM(QER.QER_LABOR)) AS Laboratorio,
                    LTRIM(RTRIM(QER.QER_ENSR)) AS Matricula_Ensaiador,
                    LTRIM(RTRIM(QAA.QAA_NOME)) AS Nome_Ensaiador,
                    LTRIM(RTRIM(QAA.QAA_LOGIN)) AS Login_Ensaiador
                FROM dbo.QER010 QER
                LEFT JOIN dbo.QE1010 QE1
                    ON QE1.D_E_L_E_T_ = ''
                   AND LTRIM(RTRIM(QE1.QE1_ENSAIO)) = LTRIM(RTRIM(QER.QER_ENSAIO))
                LEFT JOIN dbo.QE8010 QE8
                    ON QE8.D_E_L_E_T_ = ''
                   AND LTRIM(RTRIM(QE8.QE8_PRODUT)) = LTRIM(RTRIM(QER.QER_PRODUT))
                   AND LTRIM(RTRIM(QE8.QE8_REVI)) = LTRIM(RTRIM(QER.QER_REVI))
                   AND LTRIM(RTRIM(QE8.QE8_ENSAIO)) = LTRIM(RTRIM(QER.QER_ENSAIO))
                LEFT JOIN dbo.QE7010 QE7
                    ON QE7.D_E_L_E_T_ = ''
                   AND LTRIM(RTRIM(QE7.QE7_PRODUT)) = LTRIM(RTRIM(QER.QER_PRODUT))
                   AND LTRIM(RTRIM(QE7.QE7_REVI)) = LTRIM(RTRIM(QER.QER_REVI))
                   AND LTRIM(RTRIM(QE7.QE7_ENSAIO)) = LTRIM(RTRIM(QER.QER_ENSAIO))
                   AND (
                        LTRIM(RTRIM(QE7.QE7_LABOR)) = LTRIM(RTRIM(QER.QER_LABOR))
                        OR LTRIM(RTRIM(QE7.QE7_LABOR)) = ''
                   )
                LEFT JOIN dbo.QEQ010 QEQ
                    ON QEQ.D_E_L_E_T_ = ''
                   AND LTRIM(RTRIM(QEQ.QEQ_FILIAL)) = LTRIM(RTRIM(QER.QER_FILIAL))
                   AND LTRIM(RTRIM(QEQ.QEQ_CODMED)) = LTRIM(RTRIM(QER.QER_CHAVE))
                LEFT JOIN dbo.QES010 QES
                    ON QES.D_E_L_E_T_ = ''
                   AND LTRIM(RTRIM(QES.QES_FILIAL)) = LTRIM(RTRIM(QER.QER_FILIAL))
                   AND LTRIM(RTRIM(QES.QES_CODMED)) = LTRIM(RTRIM(QER.QER_CHAVE))
                LEFT JOIN dbo.QAA010 QAA
                    ON QAA.D_E_L_E_T_ = ''
                   AND QAA.QAA_FILIAL = QER.QER_FILIAL
                   AND LTRIM(RTRIM(QAA.QAA_MAT)) = LTRIM(RTRIM(QER.QER_ENSR))
                WHERE QER.D_E_L_E_T_ = ''
                  AND QER.QER_FILIAL = ?
                  AND QER.QER_FORNEC = ?
                  AND QER.QER_LOJFOR = ?
                  AND QER.QER_PRODUT = ?
                  AND QER.QER_LOTE = ?
                  AND QER.QER_NTFISC = ?
                  AND QER.QER_SERINF = ?
                  AND QER.QER_ITEMNF = ?
                ORDER BY
                    QER.QER_ENSAIO ASC,
                    QER.QER_AMOSTR ASC
                """,
                (
                    branch,
                    header.get("Codigo_Fornecedor"),
                    header.get("Loja_Fornecedor"),
                    header.get("Codigo_Produto"),
                    header.get("Lote"),
                    header.get("Nota_Fiscal"),
                    header.get("Serie_Nota_Fiscal"),
                    header.get("Item_Nota_Fiscal"),
                ),
            )
