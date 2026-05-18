# app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py
from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.application.dto.financial.list_rol_by_branch_request import (
    ListRolByBranchRequest,
)
from si_app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class FinancialRepository(BaseRepository, FinancialQueryRepositoryPort):

    def get_rol(self, request: GetRolRequest) -> dict:
        where_clause, where_params, financeiro_where_clause, financeiro_where_params = (
            self._build_rol_filters(
                branch=request.branch,
                branches=None,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        )

        branch_label = request.branch or "consolidated"
        sql = self._sql_rol_aggregate(
            where_clause=where_clause,
            financeiro_where_clause=financeiro_where_clause,
            group_by_branch=False,
            branch_label=branch_label,
        )
        params = where_params + financeiro_where_params + (branch_label,)

        with self as repo:
            result = repo.execute_one(sql, params)

        return result or self._empty_rol_row(
            branch=branch_label,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def list_rol_by_branch(self, request: ListRolByBranchRequest) -> dict[str, dict]:
        branches = [
            str(branch).strip()
            for branch in request.branches
            if branch is not None and str(branch).strip()
        ]
        if not branches:
            return {}

        where_clause, where_params, financeiro_where_clause, financeiro_where_params = (
            self._build_rol_filters(
                branch=None,
                branches=branches,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        )

        sql = self._sql_rol_aggregate(
            where_clause=where_clause,
            financeiro_where_clause=financeiro_where_clause,
            group_by_branch=True,
            branch_label=None,
        )
        params = where_params + financeiro_where_params

        with self as repo:
            rows = repo.execute_query(sql, params)

        result: dict[str, dict] = {}
        for row in rows:
            branch_code = str(row.get("branch") or "").strip()
            if branch_code:
                result[branch_code] = row

        for branch_code in branches:
            if branch_code in result:
                continue
            result[branch_code] = self._empty_rol_row(
                branch=branch_code,
                start_date=request.start_date,
                end_date=request.end_date,
            )

        return result

    def _build_rol_filters(
        self,
        *,
        branch: str | None,
        branches: list[str] | None,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str, tuple, str, tuple]:
        qb = QueryBuilder()
        qb.raw("D2.D_E_L_E_T_ = ''")

        if branch:
            qb.eq("D2.D2_FILIAL", branch)
        elif branches:
            qb.in_list("D2.D2_FILIAL", branches)

        qb.date_range("D2.D2_EMISSAO", start_date, end_date)
        where_clause, where_params = qb.build()

        financeiro_qb = QueryBuilder()
        financeiro_qb.raw("E1.D_E_L_E_T_ = ''")

        if branch:
            financeiro_qb.eq("E1.E1_FILIAL", branch)
        elif branches:
            financeiro_qb.in_list("E1.E1_FILIAL", branches)

        financeiro_where_clause, financeiro_where_params = financeiro_qb.build()
        return where_clause, where_params, financeiro_where_clause, financeiro_where_params

    def _sql_rol_aggregate(
        self,
        *,
        where_clause: str,
        financeiro_where_clause: str,
        group_by_branch: bool,
        branch_label: str | None,
    ) -> str:
        if group_by_branch:
            select_branch = "B.D2_FILIAL AS branch,"
            group_by_clause = "GROUP BY B.D2_FILIAL"
            date_select = """
            ISNULL(MIN(B.D2_EMISSAO), '') AS start_date,
            ISNULL(MAX(B.D2_EMISSAO), '') AS end_date,
            """
        else:
            select_branch = f"? AS branch,"
            group_by_clause = ""
            date_select = """
            ISNULL(MIN(B.D2_EMISSAO), '') AS start_date,
            ISNULL(MAX(B.D2_EMISSAO), '') AS end_date,
            """

        return f"""
        WITH BaseFaturamento AS
        (
            SELECT
                D2.D2_FILIAL,
                D2.D2_DOC,
                D2.D2_SERIE,
                D2.D2_CLIENTE,
                D2.D2_LOJA,
                D2.D2_EMISSAO,
                D2.D2_ITEM,
                D2.D2_COD,
                D2.D2_TES,

                F2.F2_DOC     AS F2_DOC,
                F2.F2_SERIE   AS F2_SERIE,
                F2.F2_CLIENTE AS F2_CLIENTE,
                F2.F2_LOJA    AS F2_LOJA,
                F2.F2_EMISSAO AS F2_EMISSAO,

                F4.F4_CODIGO,
                F4.F4_DUPLIC,

                ISNULL(D2.D2_TOTAL, 0) AS VALOR_ITEM,
                ISNULL(D2.D2_VALDEV, 0) AS VALOR_DEVOLUCAO,

                ISNULL(D2.D2_VALICM, 0) AS VALOR_ICMS,
                ISNULL(D2.D2_VALISS, 0) AS VALOR_ISS,
                ISNULL(D2.D2_VALPIS, 0) AS VALOR_PIS,
                ISNULL(D2.D2_VALCOF, 0) AS VALOR_COFINS,
                ISNULL(D2.D2_VALIPI, 0) AS VALOR_IPI,

                CASE
                    WHEN ISNULL(F4.F4_DUPLIC, '') = 'S'
                    THEN ISNULL(D2.D2_TOTAL, 0)
                    ELSE 0
                END AS VALOR_FATURAMENTO,

                CASE
                    WHEN F4.F4_CODIGO IS NOT NULL
                     AND ISNULL(F4.F4_DUPLIC, '') <> 'S'
                    THEN ISNULL(D2.D2_TOTAL, 0)
                    ELSE 0
                END AS VALOR_OUTROS,

                CASE
                    WHEN F4.F4_CODIGO IS NULL
                    THEN ISNULL(D2.D2_TOTAL, 0)
                    ELSE 0
                END AS VALOR_SEM_TES,

                CASE
                    WHEN ISNULL(F4.F4_DUPLIC, '') = 'S'
                    THEN ISNULL(D2.D2_DESCON, 0) + ISNULL(D2.D2_DESC, 0)
                    ELSE 0
                END AS VALOR_DESCONTO

            FROM SD2010 D2

            LEFT JOIN SF2010 F2
                ON  F2.D_E_L_E_T_ = ''
                AND F2.F2_FILIAL  = D2.D2_FILIAL
                AND F2.F2_DOC     = D2.D2_DOC
                AND F2.F2_SERIE   = D2.D2_SERIE
                AND F2.F2_CLIENTE = D2.D2_CLIENTE
                AND F2.F2_LOJA    = D2.D2_LOJA

            LEFT JOIN SF4010 F4
                ON  F4.D_E_L_E_T_ = ''
                AND F4.F4_CODIGO  = D2.D2_TES
                AND (
                        F4.F4_FILIAL = D2.D2_FILIAL
                     OR F4.F4_FILIAL = ''
                     OR F4.F4_FILIAL IS NULL
                )

            WHERE {where_clause}
        ),
        Financeiro AS
        (
            SELECT
                E1.E1_FILIAL,
                E1.E1_NUM,
                E1.E1_SERIE,
                E1.E1_CLIENTE,
                E1.E1_LOJA,
                SUM(ISNULL(E1.E1_VALOR, 0)) AS TITULO_VALOR,
                SUM(ISNULL(E1.E1_SALDO, 0)) AS TITULO_SALDO
            FROM SE1010 E1
            WHERE {financeiro_where_clause}
            GROUP BY
                E1.E1_FILIAL,
                E1.E1_NUM,
                E1.E1_SERIE,
                E1.E1_CLIENTE,
                E1.E1_LOJA
        )
        SELECT
            {select_branch}
            {date_select}
            ISNULL(SUM(B.VALOR_FATURAMENTO), 0) AS gross_revenue,
            ISNULL(SUM(B.VALOR_OUTROS), 0) AS other_values,
            ISNULL(SUM(B.VALOR_SEM_TES), 0) AS items_without_tes,
            ISNULL(SUM(B.VALOR_DEVOLUCAO), 0) AS returns,
            ISNULL(SUM(B.VALOR_DESCONTO), 0) AS discounts,

            ISNULL(SUM(B.VALOR_ICMS), 0) AS icms,
            ISNULL(SUM(B.VALOR_ISS), 0) AS iss,
            ISNULL(SUM(B.VALOR_PIS), 0) AS pis,
            ISNULL(SUM(B.VALOR_COFINS), 0) AS cofins,
            ISNULL(SUM(B.VALOR_IPI), 0) AS ipi_separated,

            ISNULL(SUM(B.VALOR_ICMS + B.VALOR_ISS + B.VALOR_PIS + B.VALOR_COFINS), 0) AS rol_taxes,

            ISNULL(SUM(B.VALOR_FATURAMENTO), 0)
            - ISNULL(SUM(B.VALOR_DEVOLUCAO), 0)
            - ISNULL(SUM(B.VALOR_DESCONTO), 0)
            - ISNULL(SUM(B.VALOR_ICMS + B.VALOR_ISS + B.VALOR_PIS + B.VALOR_COFINS), 0) AS rol,

            ISNULL(SUM(B.VALOR_FATURAMENTO), 0)
            - ISNULL(SUM(B.VALOR_DEVOLUCAO), 0)
            - ISNULL(SUM(B.VALOR_DESCONTO), 0)
            - ISNULL(SUM(B.VALOR_ICMS + B.VALOR_ISS + B.VALOR_PIS + B.VALOR_COFINS + B.VALOR_IPI), 0) AS rol_with_ipi,

            ISNULL(SUM(F.TITULO_VALOR), 0) AS financial_titles,
            ISNULL(SUM(F.TITULO_SALDO), 0) AS financial_balance

        FROM BaseFaturamento B
        LEFT JOIN Financeiro F
            ON  F.E1_FILIAL  = B.D2_FILIAL
            AND F.E1_NUM     = B.D2_DOC
            AND F.E1_SERIE   = B.D2_SERIE
            AND F.E1_CLIENTE = B.D2_CLIENTE
            AND F.E1_LOJA    = B.D2_LOJA
        {group_by_clause}
        """

    @staticmethod
    def _empty_rol_row(
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        return {
            "branch": branch,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "gross_revenue": 0,
            "other_values": 0,
            "items_without_tes": 0,
            "returns": 0,
            "discounts": 0,
            "icms": 0,
            "iss": 0,
            "pis": 0,
            "cofins": 0,
            "ipi_separated": 0,
            "rol_taxes": 0,
            "rol": 0,
            "rol_with_ipi": 0,
            "financial_titles": 0,
            "financial_balance": 0,
        }
