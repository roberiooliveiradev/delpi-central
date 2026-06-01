# app/infrastructure/persistence/totvs/nonconformity_repositories/nonconformity_query_repository.py

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

from app.domain.entities.nonconformity.nonconformity import Nonconformity
from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.domain.ports.nonconformity.nonconformity_query_repository_port import (
    NonconformityQueryRepositoryPort,
)
from app.application.models.page import Page


class NonconformityQueryRepository(BaseRepository, NonconformityQueryRepositoryPort):

    INTERNAL_TYPES = ["1"]
    EXTERNAL_TYPES = ["2", "3"]

    def list_nonconformities(
        self,
        request: ListNonconformityRequest
    ) -> Page[Nonconformity]:

        qb = QueryBuilder()

        qb.raw("D_E_L_E_T_ = ''")
        qb.eq("QI2_FILIAL", request.branch)
        qb.eq("QI2_STATUS", request.status)
        qb.eq("QI2_ITEM", request.item_code)
        qb.like("QI2_DESCR", request.description, case_insensitive=True)
        qb.date_range(
            field="QI2_OCORRE",
            start=request.date_start,
            end=request.date_end
        )

        if request.type == "internal":
            qb.in_list("QI2_TIPO", self.INTERNAL_TYPES)
        elif request.type == "external":
            qb.in_list("QI2_TIPO", self.EXTERNAL_TYPES)

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
                    QI2_FILIAL as branch,
                    QI2_FNC as code,
                    QI2_REV as revision,
                    QI2_TIPO as type_code,
                    CASE
                        WHEN QI2_TIPO = '1' THEN 'internal'
                        WHEN QI2_TIPO = '2' THEN 'customer'
                        WHEN QI2_TIPO = '3' THEN 'supplier'
                        ELSE NULL
                    END as type_label,
                    QI2_STATUS as status_code,
                    CASE
                        WHEN QI2_STATUS = '1' THEN 'registered'
                        WHEN QI2_STATUS = '2' THEN 'under_analysis'
                        WHEN QI2_STATUS = '3' THEN 'proceeds'
                        WHEN QI2_STATUS = '4' THEN 'does_not_proceed'
                        WHEN QI2_STATUS = '5' THEN 'cancelled'
                        ELSE NULL
                    END as status_label,
                    QI2_DESCR as description,
                    QI2_ITEM as item_code,
                    QI2_OP as op_code,
                    FORMAT(
                        TRY_CONVERT(date, QI2_REGIST, 112),
                        'dd/MM/yyyy'
                    ) as registered_date,
                    FORMAT(
                        TRY_CONVERT(date, QI2_OCORRE, 112),
                        'dd/MM/yyyy'
                    ) as occurrence_date,
                    QI2_PRIORI as priority_code,
                    CASE
                        WHEN QI2_PRIORI = '1' THEN 'low'
                        WHEN QI2_PRIORI = '2' THEN 'medium'
                        WHEN QI2_PRIORI = '3' THEN 'high'
                        ELSE NULL
                    END as priority_label,
                    QI2_ORIDEP as origin_department,
                    QI2_DESDEP as destination_department,
                    QI2_CODCLI as customer_code,
                    QI2_LOJCLI as customer_store,
                    QI2_CODFOR as supplier_code,
                    QI2_LOJFOR as supplier_store,
                    QI2_QTDPRO as produced_quantity,
                    QI2_QTDDEV as returned_quantity
                {base_sql}
            """

            if request.page_size:
                page = request.page or 1
                offset = (page - 1) * request.page_size

                sql = f"""
                    {select_sql}
                    ORDER BY QI2_OCORRE DESC, QI2_FNC DESC, QI2_REV DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """

                final_params = list(params)
                final_params.extend([offset, request.page_size])

            else:
                page = 1
                sql = f"""
                    {select_sql}
                    ORDER BY QI2_OCORRE DESC, QI2_FNC DESC, QI2_REV DESC
                """
                final_params = params

            rows = repo.execute_query(sql, final_params)

            items = [
                Nonconformity(**row)
                for row in rows
            ]

            return Page(
                items=items,
                total=total,
                page=page,
                page_size=request.page_size or total
            )

    def sum_returned_quantity(
        self,
        request: ListNonconformityRequest,
        *,
        occurrence_date_start: str | None = None,
        occurrence_date_end: str | None = None,
    ) -> tuple[float, int]:
        qb = QueryBuilder()

        qb.raw("D_E_L_E_T_ = ''")
        qb.eq("QI2_FILIAL", request.branch)
        qb.eq("QI2_STATUS", request.status)
        qb.eq("QI2_ITEM", request.item_code)
        qb.like("QI2_DESCR", request.description, case_insensitive=True)
        qb.date_range(
            field="QI2_OCORRE",
            start=occurrence_date_start,
            end=occurrence_date_end,
        )

        if request.type == "internal":
            qb.in_list("QI2_TIPO", self.INTERNAL_TYPES)
        elif request.type == "external":
            qb.in_list("QI2_TIPO", self.EXTERNAL_TYPES)

        where_clause, params = qb.build()

        sql = f"""
            SELECT
                ISNULL(
                    SUM(
                        COALESCE(
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
                            0
                        )
                    ),
                    0
                ) AS total_returned,
                COUNT(1) AS registros
            FROM QI2010
            WHERE {where_clause}
        """

        with self as repo:
            row = repo.execute_one(sql, params) or {}

        return (
            float(row.get("total_returned") or 0),
            int(row.get("registros") or 0),
        )