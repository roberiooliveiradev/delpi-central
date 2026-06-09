from datetime import datetime, timedelta

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

from app.application.models.page import Page
from app.domain.entities.ppm.ppm_summary import PpmSummary
from app.domain.entities.ppm.ppm_item import PpmItem
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_production_sql import (
    QTD_PRODUZIDA_OP_EXPR,
    SC2_OP_JOIN,
)


class PpmQueryRepository(BaseRepository, PpmQueryRepositoryPort):

    def _type_filter(self, ppm_type: str) -> str:
        if ppm_type == "internal":
            return "QI2_TIPO = '1'"

        if ppm_type == "external":
            return "QI2_TIPO = '2'"

        raise ValueError("ppm_type deve ser internal ou external")

    def _to_protheus_date(self, value: str | None) -> str | None:
        return QueryBuilder().convert_date_to_protheus(value)

    def _exclusive_end_date(self, value: str | None) -> str | None:
        protheus_date = self._to_protheus_date(value)

        if not protheus_date:
            return None

        parsed = datetime.strptime(protheus_date, "%Y%m%d")
        return (parsed + timedelta(days=1)).strftime("%Y%m%d")

    def _map_ppm_item(self, row: dict) -> PpmItem:
        """Mapeia linha SQL para entidade (ignora colunas extras do SELECT)."""
        return PpmItem(
            branch=str(row.get("branch") or "").strip(),
            registered_date=row.get("registered_date"),
            code=str(row.get("code") or "").strip(),
            revision=str(row.get("revision") or "").strip(),
            item_code=row.get("item_code"),
            description=row.get("description"),
            returned_quantity_original=row.get("returned_quantity_original"),
            returned_quantity_un=float(row.get("returned_quantity_un") or 0),
        )

    def get_summary(self, request) -> PpmSummary:
        date_start = self._to_protheus_date(request.date_start)
        date_end_exclusive = self._exclusive_end_date(request.date_end)

        qb_nc = QueryBuilder()
        qb_nc.raw("D_E_L_E_T_ = ' '")

        if request.branch:
            qb_nc.eq("QI2_FILIAL", request.branch)

        if date_start:
            qb_nc.gte("QI2_OCORRE", date_start)

        if date_end_exclusive:
            qb_nc.lt("QI2_OCORRE", date_end_exclusive)

        qb_nc.raw(self._type_filter(request.type))

        where_nc, params_nc = qb_nc.build()

        prod_branch_filter_g2 = ""
        prod_branch_filter_sh6 = ""
        prod_params = []

        if request.branch:
            prod_branch_filter_g2 = "AND G2.G2_FILIAL = ?"
            prod_params.append(request.branch)

        prod_params.extend([
            date_end_exclusive,
            date_start,
        ])

        if request.branch:
            prod_branch_filter_sh6 = "AND SH6.H6_FILIAL = ?"
            prod_params.append(request.branch)

        prod_params.extend([
            date_start,
            date_end_exclusive,
        ])

        sql = f"""
            WITH nc AS (
                SELECT
                    SUM(
                        COALESCE(
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
                            0
                        )
                    ) AS total_devolvido_un
                FROM QI2010
                WHERE {where_nc}
            ),
            roteiro_final AS (
                SELECT
                    G2.G2_FILIAL,
                    G2.G2_PRODUTO,
                    MAX(G2.G2_OPERAC) AS operacao_final_roteiro
                FROM SG2010 G2
                WHERE
                    G2.D_E_L_E_T_ = ' '
                    {prod_branch_filter_g2}
                    AND (G2.G2_DTINI = '' OR G2.G2_DTINI < ?)
                    AND (G2.G2_DTFIM = '' OR G2.G2_DTFIM >= ?)
                GROUP BY
                    G2.G2_FILIAL,
                    G2.G2_PRODUTO
            ),
            apont_final AS (
                SELECT
                    SH6.H6_FILIAL,
                    SH6.H6_OP,
                    SH6.H6_PRODUTO,
                    SH6.H6_OPERAC,
                    SB1.B1_GRUPO,
                    {QTD_PRODUZIDA_OP_EXPR.strip()} AS qtd_produzida_op
                FROM SH6010 SH6
                INNER JOIN roteiro_final RF
                    ON RF.G2_FILIAL = SH6.H6_FILIAL
                   AND RF.G2_PRODUTO = SH6.H6_PRODUTO
                   AND RF.operacao_final_roteiro = SH6.H6_OPERAC
                INNER JOIN SB1010 SB1
                    ON SB1.B1_COD = SH6.H6_PRODUTO
                   AND SB1.D_E_L_E_T_ = ' '
                   AND SB1.B1_TIPO = 'PA'
                {SC2_OP_JOIN}
                WHERE
                    SH6.D_E_L_E_T_ = ' '
                    {prod_branch_filter_sh6}
                    AND SH6.H6_TIPO = 'P'
                    AND SH6.H6_OP <> ''
                    AND SH6.H6_PRODUTO <> ''
                    AND SH6.H6_DTAPONT >= ?
                    AND SH6.H6_DTAPONT < ?
                GROUP BY
                    SH6.H6_FILIAL,
                    SH6.H6_OP,
                    SH6.H6_PRODUTO,
                    SH6.H6_OPERAC,
                    SB1.B1_GRUPO
            ),
            prod AS (
                SELECT
                    SUM(qtd_produzida_op) AS total_produzido_milheiro
                FROM apont_final
            )
            SELECT
                ISNULL(nc.total_devolvido_un, 0) AS total_devolvido_un,
                ISNULL(prod.total_produzido_milheiro, 0) AS total_produzido_milheiro,
                ISNULL(prod.total_produzido_milheiro, 0) * 1000 AS total_produzido_un,
                CASE
                    WHEN ISNULL(prod.total_produzido_milheiro, 0) = 0 THEN 0
                    ELSE (ISNULL(nc.total_devolvido_un, 0) / (prod.total_produzido_milheiro * 1000.0)) * 1000000.0
                END AS ppm
            FROM nc
            CROSS JOIN prod
        """

        final_params = tuple(list(params_nc) + prod_params)

        with self as repo:
            row = repo.execute_one(sql, final_params) or {}

        return PpmSummary(
            type=request.type,
            branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
            total_devolvido_un=float(row.get("total_devolvido_un") or 0),
            total_produzido_milheiro=float(row.get("total_produzido_milheiro") or 0),
            total_produzido_un=float(row.get("total_produzido_un") or 0),
            ppm=float(row.get("ppm") or 0),
        )

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        if ppm_type not in {"internal", "external"}:
            raise ValueError("ppm_type deve ser internal ou external")

        date_start_protheus = self._to_protheus_date(date_start)
        date_end_exclusive = self._exclusive_end_date(date_end)

        nc_filters = [
            "D_E_L_E_T_ = ' '",
            self._type_filter(ppm_type),
            "NULLIF(LTRIM(RTRIM(QI2_FILIAL)), '') IS NOT NULL",
        ]
        nc_params: list[str] = []

        if date_start_protheus:
            nc_filters.append("QI2_OCORRE >= ?")
            nc_params.append(date_start_protheus)

        if date_end_exclusive:
            nc_filters.append("QI2_OCORRE < ?")
            nc_params.append(date_end_exclusive)

        prod_filters = [
            "D_E_L_E_T_ = ' '",
            "H6_TIPO = 'P'",
            "H6_OP <> ''",
            "H6_PRODUTO <> ''",
            "NULLIF(LTRIM(RTRIM(H6_FILIAL)), '') IS NOT NULL",
        ]
        prod_params: list[str] = []

        if date_start_protheus:
            prod_filters.append("H6_DTAPONT >= ?")
            prod_params.append(date_start_protheus)

        if date_end_exclusive:
            prod_filters.append("H6_DTAPONT < ?")
            prod_params.append(date_end_exclusive)

        sql = f"""
            SELECT DISTINCT branch
            FROM (
                SELECT
                    LTRIM(RTRIM(QI2_FILIAL)) AS branch
                FROM QI2010
                WHERE {' AND '.join(nc_filters)}

                UNION

                SELECT
                    LTRIM(RTRIM(H6_FILIAL)) AS branch
                FROM SH6010
                WHERE {' AND '.join(prod_filters)}
            ) branches
            WHERE branch <> ''
            ORDER BY branch
        """

        params = tuple(nc_params + prod_params)

        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            str(row.get("branch")).strip()
            for row in rows
            if row.get("branch") and str(row.get("branch")).strip()
        ]

    def list_items(self, request) -> Page[PpmItem]:
        date_start = self._to_protheus_date(request.date_start)
        date_end_exclusive = self._exclusive_end_date(request.date_end)

        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ' '")

        if request.branch:
            qb.eq("QI2_FILIAL", request.branch)

        if date_start:
            qb.gte("QI2_OCORRE", date_start)

        if date_end_exclusive:
            qb.lt("QI2_OCORRE", date_end_exclusive)

        qb.raw(self._type_filter(request.type))

        where_clause, params = qb.build()

        base_sql = f"""
            FROM QI2010
            WHERE {where_clause}
        """

        with self as repo:
            total_sql = f"""
                SELECT COUNT(1)
                {base_sql}
            """
            total = repo.execute_scalar(total_sql, params)

            select_sql = f"""
                SELECT
                    QI2_FILIAL AS branch,
                    FORMAT(TRY_CONVERT(date, QI2_OCORRE, 112), 'dd/MM/yyyy') AS registered_date,
                    QI2_FNC AS code,
                    QI2_REV AS revision,
                    QI2_TIPO AS ppm_type,
                    CASE
                        WHEN QI2_TIPO = '1' THEN 'interno'
                        WHEN QI2_TIPO = '2' THEN 'externo_cliente'
                        WHEN QI2_TIPO = '3' THEN 'fornecedor'
                        ELSE 'outro'
                    END AS ppm_type_description,
                    QI2_ITEM AS item_code,
                    QI2_DESCR AS description,
                    QI2_QTDDEV AS returned_quantity_original,
                    CAST(
                        COALESCE(
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
                            0
                        ) AS FLOAT
                    ) AS returned_quantity_un
                {base_sql}
            """

            if request.page_size:
                page = request.page or 1
                offset = (page - 1) * request.page_size

                sql = f"""
                    {select_sql}
                    ORDER BY QI2_OCORRE DESC, QI2_FNC DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """

                final_params = list(params)
                final_params.extend([offset, request.page_size])
            else:
                page = 1

                sql = f"""
                    {select_sql}
                    ORDER BY QI2_OCORRE DESC, QI2_FNC DESC
                """

                final_params = params

            rows = repo.execute_query(sql, final_params)

            items = [self._map_ppm_item(row) for row in rows]

            return Page(
                items=items,
                total=total,
                page=page,
                page_size=request.page_size or total,
            )