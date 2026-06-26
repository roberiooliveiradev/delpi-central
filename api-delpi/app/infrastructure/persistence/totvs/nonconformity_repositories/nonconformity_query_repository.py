# app/infrastructure/persistence/totvs/nonconformity_repositories/nonconformity_query_repository.py

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.quality.qi2_record_sql import (
    qi2_detailed_description_sql,
    qi2_from_with_customer,
    qi2_prefix_where_clause,
)
from app.domain.services.quality.nonconformity_display_service import (
    format_nonconformity_code,
    normalize_memo_text,
    normalize_optional_text,
    resolve_nonconformity_status_label,
    resolve_nonconformity_type_label,
)

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

    def _map_nonconformity(self, row: dict) -> Nonconformity:
        code = str(row.get("code") or "").strip()
        type_code = str(row.get("type_code") or "").strip()
        status_code = str(row.get("status_code") or "").strip()
        return Nonconformity(
            branch=str(row.get("branch") or "").strip(),
            code=code,
            revision=str(row.get("revision") or "").strip(),
            type_code=type_code,
            code_display=format_nonconformity_code(code),
            type_label=resolve_nonconformity_type_label(type_code),
            status_code=status_code or None,
            status_label=resolve_nonconformity_status_label(status_code),
            description=normalize_optional_text(row.get("description")),
            detailed_description=normalize_memo_text(row.get("detailed_description")),
            item_code=normalize_optional_text(row.get("item_code")),
            op_code=normalize_optional_text(row.get("op_code")),
            registered_date=row.get("registered_date"),
            occurrence_date=row.get("occurrence_date"),
            priority_code=row.get("priority_code"),
            priority_label=row.get("priority_label"),
            origin_department=normalize_optional_text(row.get("origin_department")),
            destination_department=normalize_optional_text(row.get("destination_department")),
            customer_code=normalize_optional_text(row.get("customer_code")),
            customer_store=normalize_optional_text(row.get("customer_store")),
            customer_name=normalize_optional_text(row.get("customer_name")),
            supplier_code=normalize_optional_text(row.get("supplier_code")),
            supplier_store=normalize_optional_text(row.get("supplier_store")),
            produced_quantity=row.get("produced_quantity"),
            returned_quantity=row.get("returned_quantity"),
        )

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
            {qi2_from_with_customer(table_alias="nc")}
            WHERE {qi2_prefix_where_clause(where_clause, table_alias="nc")}
        """

        with self as repo:

            total_sql = f"""
                SELECT COUNT(1)
                {base_sql}
            """

            total = repo.execute_scalar(total_sql, params)

            select_sql = f"""
                SELECT
                    nc.QI2_FILIAL as branch,
                    nc.QI2_FNC as code,
                    nc.QI2_REV as revision,
                    nc.QI2_TIPO as type_code,
                    nc.QI2_STATUS as status_code,
                    nc.QI2_DESCR as description,
                    {qi2_detailed_description_sql(table_alias="nc")},
                    nc.QI2_ITEM as item_code,
                    nc.QI2_OP as op_code,
                    FORMAT(
                        TRY_CONVERT(date, nc.QI2_REGIST, 112),
                        'dd/MM/yyyy'
                    ) as registered_date,
                    FORMAT(
                        TRY_CONVERT(date, nc.QI2_OCORRE, 112),
                        'dd/MM/yyyy'
                    ) as occurrence_date,
                    nc.QI2_PRIORI as priority_code,
                    CASE
                        WHEN nc.QI2_PRIORI = '1' THEN 'low'
                        WHEN nc.QI2_PRIORI = '2' THEN 'medium'
                        WHEN nc.QI2_PRIORI = '3' THEN 'high'
                        ELSE NULL
                    END as priority_label,
                    nc.QI2_ORIDEP as origin_department,
                    nc.QI2_DESDEP as destination_department,
                    NULLIF(LTRIM(RTRIM(nc.QI2_CODCLI)), '') as customer_code,
                    NULLIF(LTRIM(RTRIM(nc.QI2_LOJCLI)), '') as customer_store,
                    NULLIF(LTRIM(RTRIM(SA1.A1_NOME)), '') as customer_name,
                    nc.QI2_CODFOR as supplier_code,
                    nc.QI2_LOJFOR as supplier_store,
                    nc.QI2_QTDPRO as produced_quantity,
                    nc.QI2_QTDDEV as returned_quantity
                {base_sql}
            """

            if request.page_size:
                page = request.page or 1
                offset = (page - 1) * request.page_size

                sql = f"""
                    {select_sql}
                    ORDER BY nc.QI2_OCORRE DESC, nc.QI2_FNC DESC, nc.QI2_REV DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """

                final_params = list(params)
                final_params.extend([offset, request.page_size])

            else:
                page = 1
                sql = f"""
                    {select_sql}
                    ORDER BY nc.QI2_OCORRE DESC, nc.QI2_FNC DESC, nc.QI2_REV DESC
                """
                final_params = params

            rows = repo.execute_query(sql, final_params)

            items = [
                self._map_nonconformity(row)
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