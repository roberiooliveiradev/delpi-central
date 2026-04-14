from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

from app.application.models.page import Page
from app.domain.entities.ppm.ppm_summary import PpmSummary
from app.domain.entities.ppm.ppm_item import PpmItem
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class PpmQueryRepository(BaseRepository, PpmQueryRepositoryPort):

    def _type_filter(self, ppm_type: str) -> str:
        if ppm_type == "internal":
            return "QI2_TIPO = '1'"
        return "QI2_TIPO IN ('2','3')"

    def get_summary(self, request) -> PpmSummary:
        qb_nc = QueryBuilder()
        qb_nc.raw("D_E_L_E_T_ = ''")
        if request.branch:
            qb_nc.eq("QI2_FILIAL", request.branch)
        qb_nc.date_range("QI2_REGIST", request.date_start, request.date_end)
        qb_nc.raw(self._type_filter(request.type))
        where_nc, params_nc = qb_nc.build()

        qb_prod = QueryBuilder()
        qb_prod.raw("D_E_L_E_T_ = ''")
        if request.branch:
            qb_prod.eq("H6_FILIAL", request.branch)
        qb_prod.date_range("H6_DATAINI", request.date_start, request.date_end)
        where_prod, params_prod = qb_prod.build()

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
            prod AS (
                SELECT
                    SUM(ISNULL(H6_QTDPROD, 0)) AS total_produzido_milheiro
                FROM SH6010
                WHERE {where_prod}
            )
            SELECT
                ISNULL(nc.total_devolvido_un, 0) AS total_devolvido_un,
                ISNULL(prod.total_produzido_milheiro, 0) AS total_produzido_milheiro,
                ISNULL(prod.total_produzido_milheiro, 0) * 1000 AS total_produzido_un,
                CASE
                    WHEN ISNULL(prod.total_produzido_milheiro, 0) = 0 THEN 0
                    ELSE (ISNULL(nc.total_devolvido_un, 0) / prod.total_produzido_milheiro) * 1000.0
                END AS ppm
            FROM nc
            CROSS JOIN prod
        """

        with self as repo:
            row = repo.execute_one(sql, tuple(list(params_nc) + list(params_prod))) or {}

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

    def list_items(self, request) -> Page[PpmItem]:
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")
        if request.branch:
            qb.eq("QI2_FILIAL", request.branch)
        qb.date_range("QI2_REGIST", request.date_start, request.date_end)
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
                    FORMAT(TRY_CONVERT(date, QI2_REGIST, 112), 'dd/MM/yyyy') AS registered_date,
                    QI2_FNC AS code,
                    QI2_REV AS revision,
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
                    ORDER BY QI2_REGIST DESC, QI2_FNC DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """
                final_params = list(params)
                final_params.extend([offset, request.page_size])
            else:
                page = 1
                sql = f"""
                    {select_sql}
                    ORDER BY QI2_REGIST DESC, QI2_FNC DESC
                """
                final_params = params

            rows = repo.execute_query(sql, final_params)

            items = [PpmItem(**row) for row in rows]

            return Page(
                items=items,
                total=total,
                page=page,
                page_size=request.page_size or total
            )