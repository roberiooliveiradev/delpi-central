from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from si_app.domain.entities.commercial.new_clients_rol_pct import NewClientsRolPct
from si_app.domain.ports.commercial.new_clients_rol_pct_repository_port import NewClientsRolPctRepositoryPort


class NewClientsRolPctRepository(BaseRepository, NewClientsRolPctRepositoryPort):

    def get_new_clients_rol_pct(
        self,
        request: NewClientsRolPctRequest
    ) -> NewClientsRolPct:
        primeira_ov_qb = QueryBuilder()
        primeira_ov_qb.raw("AD1.D_E_L_E_T_ = ''")
        if request.branch:
            primeira_ov_qb.eq("AD1.AD1_FILIAL", request.branch)
        primeira_ov_qb.raw("AD1.AD1_CODCLI <> ''")
        primeira_ov_qb.raw("AD1.AD1_LOJCLI <> ''")
        primeira_ov_where, primeira_ov_params = primeira_ov_qb.build()

        periodo_ov_qb = QueryBuilder()
        periodo_ov_qb.date_range("PRIMEIRA_DATA", request.start_date, request.end_date)
        periodo_ov_where, periodo_ov_params = periodo_ov_qb.build()

        vendas_qb = QueryBuilder()
        vendas_qb.raw("D2.D_E_L_E_T_ = ''")
        if request.branch:
            vendas_qb.eq("D2.D2_FILIAL", request.branch)
        vendas_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        vendas_where, vendas_params = vendas_qb.build()

        exists_qb = QueryBuilder()
        exists_qb.date_range("D1X.D1_DTDIGIT", request.start_date, request.end_date)
        exists_where, exists_params = exists_qb.build()

        dev_qb = QueryBuilder()
        dev_qb.raw("D1.D_E_L_E_T_ = ''")
        if request.branch:
            dev_qb.eq("D1.D1_FILIAL", request.branch)
        dev_qb.date_range("D1.D1_DTDIGIT", request.start_date, request.end_date)
        dev_where, dev_params = dev_qb.build()

        sql = f"""
            WITH primeira_ov_cliente AS (
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI,
                    MIN(AD1.AD1_DATA) AS PRIMEIRA_DATA
                FROM AD1010 AD1
                WHERE {primeira_ov_where}
                GROUP BY
                    AD1.AD1_FILIAL,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI
            ),

            novos_clientes AS (
                SELECT
                    AD1_FILIAL,
                    AD1_CODCLI,
                    AD1_LOJCLI,
                    PRIMEIRA_DATA
                FROM primeira_ov_cliente
                WHERE {periodo_ov_where}
            ),

            VENDAS AS (
                SELECT
                    D2.D2_FILIAL,
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    SUM(CONVERT(FLOAT,
                        ISNULL(D2.D2_TOTAL, 0)
                        - ISNULL(D2.D2_VALICM, 0)
                        - ISNULL(D2.D2_VALIMP5, 0)
                        - ISNULL(D2.D2_VALIMP6, 0)
                    )) AS VLR_VENDA

                FROM SD2010 D2

                LEFT JOIN SA1010 A1
                    ON  A1.D_E_L_E_T_ = ''
                    AND A1.A1_COD  = D2.D2_CLIENTE
                    AND A1.A1_LOJA = D2.D2_LOJA

                LEFT JOIN SF4010 F4
                    ON  F4.D_E_L_E_T_ = ''
                    AND F4.F4_CODIGO = D2.D2_TES
                    AND (
                            F4.F4_FILIAL = D2.D2_FILIAL
                         OR F4.F4_FILIAL = ''
                         OR F4.F4_FILIAL IS NULL
                    )

                WHERE {vendas_where}
                    AND ISNULL(A1.A1_NOME, '') <> ''
                    AND ISNULL(D2.D2_TIPO, '') <> 'D'

                    AND (
                        D2.D2_CF NOT IN ('5911', '6151')
                        OR (
                            D2.D2_FILIAL = '01'
                            AND D2.D2_CF IN ('5911', '6911')
                            AND D2.D2_COD LIKE '90%'
                            AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND D2.D2_UM = 'MI'
                        )
                    )

                    AND (
                        ISNULL(F4.F4_DUPLIC, '') = 'S'

                        OR (
                            ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND ISNULL(F4.F4_FINALID, '') = 'BAIXA ESTOQUE'
                            AND D2.D2_CF  = '5927'
                            AND D2.D2_UM  = 'MI'
                            AND EXISTS (
                                SELECT 1
                                FROM SD1010 D1X
                                WHERE
                                    D1X.D_E_L_E_T_ = ''
                                    AND D1X.D1_FILIAL  = D2.D2_FILIAL
                                    AND D1X.D1_FORNECE = D2.D2_CLIENTE
                                    AND D1X.D1_LOJA    = D2.D2_LOJA
                                    AND {exists_where}
                                    AND (
                                        D1X.D1_CF IN ('1201', '2201')
                                        OR D1X.D1_TIPO = 'D'
                                    )
                            )
                        )

                        OR (
                            D2.D2_FILIAL = '01'
                            AND D2.D2_CF IN ('5911', '6911')
                            AND D2.D2_COD LIKE '90%'
                            AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND D2.D2_UM = 'MI'
                        )
                    )

                GROUP BY D2.D2_FILIAL, D2.D2_CLIENTE, D2.D2_LOJA
            ),

            DEVOLUCOES AS (
                SELECT
                    D1.D1_FILIAL,
                    D1.D1_FORNECE,
                    D1.D1_LOJA,
                    SUM(CONVERT(FLOAT,
                        ISNULL(D1.D1_TOTAL, 0)
                        - ISNULL(D1.D1_VALICM, 0)
                        - ISNULL(D1.D1_VALIMP5, 0)
                        - ISNULL(D1.D1_VALIMP6, 0)
                    )) AS VLR_DEVOLUCAO

                FROM SD1010 D1

                WHERE {dev_where}
                    AND (
                        D1.D1_CF IN ('1201', '2201')
                        OR D1.D1_TIPO = 'D'
                    )

                GROUP BY D1.D1_FILIAL, D1.D1_FORNECE, D1.D1_LOJA
            ),

            ROL_POR_CLIENTE AS (
                SELECT
                    ISNULL(V.D2_FILIAL, D.D1_FILIAL)    AS FILIAL,
                    ISNULL(V.D2_CLIENTE, D.D1_FORNECE)   AS COD_CLIENTE,
                    ISNULL(V.D2_LOJA, D.D1_LOJA)         AS LOJA,
                    ISNULL(V.VLR_VENDA, 0)
                    - ISNULL(D.VLR_DEVOLUCAO, 0)          AS ROL_CLIENTE
                FROM VENDAS V
                FULL OUTER JOIN DEVOLUCOES D
                    ON  D.D1_FILIAL  = V.D2_FILIAL
                    AND D.D1_FORNECE = V.D2_CLIENTE
                    AND D.D1_LOJA    = V.D2_LOJA
            ),

            rol_total AS (
                SELECT ISNULL(SUM(ROL_CLIENTE), 0) AS TOTAL_ROL
                FROM ROL_POR_CLIENTE
            ),

            rol_novos_clientes AS (
                SELECT ISNULL(SUM(RC.ROL_CLIENTE), 0) AS NEW_CLIENTS_ROL
                FROM ROL_POR_CLIENTE RC
                INNER JOIN novos_clientes NC
                    ON  NC.AD1_FILIAL  = RC.FILIAL
                    AND NC.AD1_CODCLI  = RC.COD_CLIENTE
                    AND NC.AD1_LOJCLI  = RC.LOJA
            )

            SELECT
                ? AS branch,
                ? AS start_date,
                ? AS end_date,
                RT.TOTAL_ROL AS total_rol,
                RN.NEW_CLIENTS_ROL AS new_clients_rol,
                CAST(
                    CASE
                        WHEN RT.TOTAL_ROL = 0 THEN 0
                        ELSE RN.NEW_CLIENTS_ROL * 100.0 / RT.TOTAL_ROL
                    END
                AS DECIMAL(10, 2)) AS new_clients_rol_pct
            FROM rol_total RT
            CROSS JOIN rol_novos_clientes RN
        """

        params = (
            primeira_ov_params
            + periodo_ov_params
            + vendas_params
            + exists_params
            + dev_params
            + (
                request.branch or "consolidated",
                request.start_date or "",
                request.end_date or "",
            )
        )

        with self:
            row = self.execute_one(sql, params)

        return NewClientsRolPct(
            branch=(row or {}).get("branch") or request.branch,
            start_date=(row or {}).get("start_date") or request.start_date,
            end_date=(row or {}).get("end_date") or request.end_date,
            total_rol=float((row or {}).get("total_rol") or 0),
            new_clients_rol=float((row or {}).get("new_clients_rol") or 0),
            new_clients_rol_pct=(row or {}).get("new_clients_rol_pct") or 0,
        )
