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
        faturamento_qb = QueryBuilder()
        faturamento_qb.raw("D2.D_E_L_E_T_ = ''")

        if request.branch:
            faturamento_qb.eq("D2.D2_FILIAL", request.branch)

        faturamento_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)

        faturamento_where_clause, faturamento_where_params = faturamento_qb.build()

        primeira_ov_qb = QueryBuilder()
        primeira_ov_qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            primeira_ov_qb.eq("AD1.AD1_FILIAL", request.branch)

        primeira_ov_qb.raw("AD1.AD1_CODCLI <> ''")
        primeira_ov_qb.raw("AD1.AD1_LOJCLI <> ''")

        primeira_ov_where_clause, primeira_ov_where_params = primeira_ov_qb.build()

        periodo_primeira_ov_qb = QueryBuilder()
        periodo_primeira_ov_qb.date_range("PRIMEIRA_DATA", request.start_date, request.end_date)

        periodo_primeira_ov_where_clause, periodo_primeira_ov_where_params = periodo_primeira_ov_qb.build()

        sql = f"""
            WITH primeira_ov_cliente AS (
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI,
                    MIN(AD1.AD1_DATA) AS PRIMEIRA_DATA
                FROM AD1010 AD1
                WHERE {primeira_ov_where_clause}
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
                WHERE {periodo_primeira_ov_where_clause}
            ),
            base_faturamento AS (
                SELECT
                    D2.D2_FILIAL,
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    ISNULL(D2.D2_TOTAL, 0) AS VALOR_ITEM,
                    ISNULL(D2.D2_VALDEV, 0) AS VALOR_DEVOLUCAO,
                    ISNULL(D2.D2_VALICM, 0) AS VALOR_ICMS,
                    ISNULL(D2.D2_VALISS, 0) AS VALOR_ISS,
                    ISNULL(D2.D2_VALPIS, 0) AS VALOR_PIS,
                    ISNULL(D2.D2_VALCOF, 0) AS VALOR_COFINS,
                    ISNULL(D2.D2_VALIPI, 0) AS VALOR_IPI,
                    ISNULL(D2.D2_DESCON, 0) + ISNULL(D2.D2_DESC, 0) AS VALOR_DESCONTO,

                    CASE
                        WHEN ISNULL(F4.F4_DUPLIC, '') = 'S'
                        THEN ISNULL(D2.D2_TOTAL, 0)
                        ELSE 0
                    END AS VALOR_FATURAMENTO
                FROM SD2010 D2
                LEFT JOIN SF4010 F4
                    ON  F4.D_E_L_E_T_ = ''
                    AND F4.F4_CODIGO  = D2.D2_TES
                    AND (
                            F4.F4_FILIAL = D2.D2_FILIAL
                         OR F4.F4_FILIAL = ''
                         OR F4.F4_FILIAL IS NULL
                    )
                WHERE {faturamento_where_clause}
            ),
            rol_total AS (
                SELECT
                    ISNULL(SUM(VALOR_FATURAMENTO), 0)
                    - ISNULL(SUM(VALOR_DEVOLUCAO), 0)
                    - ISNULL(SUM(VALOR_DESCONTO), 0)
                    - ISNULL(SUM(VALOR_ICMS + VALOR_ISS + VALOR_PIS + VALOR_COFINS + VALOR_IPI), 0) AS TOTAL_ROL
                FROM base_faturamento
            ),
            rol_novos_clientes AS (
                SELECT
                    ISNULL(SUM(BF.VALOR_FATURAMENTO), 0)
                    - ISNULL(SUM(BF.VALOR_DEVOLUCAO), 0)
                    - ISNULL(SUM(BF.VALOR_DESCONTO), 0)
                    - ISNULL(SUM(BF.VALOR_ICMS + BF.VALOR_ISS + BF.VALOR_PIS + BF.VALOR_COFINS + BF.VALOR_IPI), 0) AS NEW_CLIENTS_ROL
                FROM base_faturamento BF
                INNER JOIN novos_clientes NC
                    ON NC.AD1_FILIAL = BF.D2_FILIAL
                AND NC.AD1_CODCLI = BF.D2_CLIENTE
                AND NC.AD1_LOJCLI = BF.D2_LOJA
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
            primeira_ov_where_params
            + periodo_primeira_ov_where_params
            + faturamento_where_params
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