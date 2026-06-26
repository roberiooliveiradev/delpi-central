from datetime import datetime, timedelta

from app.application.models.page import Page
from app.domain.entities.ppm.ppm_item import PpmItem
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.services.quality.ppm_query_cache import (
    get_cached_ppm_summary,
    ppm_summary_cache_key,
    set_cached_ppm_summary,
)
from app.domain.entities.ppm.ppm_summary import PpmSummary
from app.domain.entities.ppm.produced_quantity import (
    ProducedQuantityByProduct,
    ProducedQuantityItem,
    ProducedQuantityReport,
)
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_inspection_sql_builder import (
    append_apont_date_params,
    build_inspection_apont_ctes,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_nc_query import (
    build_nc_where_clause,
)
from app.infrastructure.persistence.totvs.quality.qi2_record_sql import (
    qi2_detailed_description_sql,
    qi2_from_with_customer,
    qi2_prefix_where_clause,
)
from app.domain.services.quality.nonconformity_display_service import (
    format_nonconformity_code,
    normalize_memo_text,
    normalize_optional_text,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_protheus_dates import (
    exclusive_end_date,
    to_protheus_date,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class PpmQueryRepository(BaseRepository, PpmQueryRepositoryPort):

    def _map_ppm_item(self, row: dict) -> PpmItem:
        """Mapeia linha SQL para entidade (ignora colunas extras do SELECT)."""
        code = str(row.get("code") or "").strip()
        return PpmItem(
            branch=str(row.get("branch") or "").strip(),
            registered_date=row.get("registered_date"),
            code=code,
            code_display=format_nonconformity_code(code),
            revision=str(row.get("revision") or "").strip(),
            item_code=normalize_optional_text(row.get("item_code")),
            description=normalize_optional_text(row.get("description")),
            detailed_description=normalize_memo_text(row.get("detailed_description")),
            customer_code=normalize_optional_text(row.get("customer_code")),
            customer_store=normalize_optional_text(row.get("customer_store")),
            customer_name=normalize_optional_text(row.get("customer_name")),
            returned_quantity_original=row.get("returned_quantity_original"),
            returned_quantity_un=float(row.get("returned_quantity_un") or 0),
        )

    def _resolve_date_range(
        self,
        date_start: str | None,
        date_end: str | None,
    ) -> tuple[str | None, str | None]:
        return to_protheus_date(date_start), exclusive_end_date(date_end)

    def get_summary(self, request) -> PpmSummary:
        cache_key = ppm_summary_cache_key(request)
        cached = get_cached_ppm_summary(cache_key)
        if cached is not None:
            return cached

        summary = self._load_summary(request)
        set_cached_ppm_summary(cache_key, summary)
        return summary

    def _load_summary(self, request) -> PpmSummary:
        date_start, date_end_exclusive = self._resolve_date_range(
            request.date_start,
            request.date_end,
        )

        where_nc, params_nc = build_nc_where_clause(
            ppm_type=request.type,
            branch=request.branch,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
        )

        ctes = build_inspection_apont_ctes(branch=request.branch)
        prod_params = append_apont_date_params(
            ctes.params,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
        )

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
                FROM QI2010 WITH (NOLOCK)
                WHERE {where_nc}
            ),
            {ctes.ct_inspecao_cte.strip()},
            {ctes.apont_inspecao_cte.strip()},
            prod AS (
                SELECT
                    SUM(qtd_produzida_op) AS total_produzido_milheiro
                FROM apont_inspecao
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

    def list_produced_quantity(self, request) -> ProducedQuantityReport:
        date_start, date_end_exclusive = self._resolve_date_range(
            request.date_start,
            request.date_end,
        )

        if not date_start or not date_end_exclusive:
            raise ValueError("date_start e date_end são obrigatórios.")

        ctes = build_inspection_apont_ctes(
            branch=request.branch,
            product_codes=request.products,
        )
        params = tuple(
            append_apont_date_params(
                ctes.params,
                date_start=date_start,
                date_end_exclusive=date_end_exclusive,
            )
        )

        sql = f"""
            WITH
            {ctes.ct_inspecao_cte.strip()},
            {ctes.apont_inspecao_cte.strip()}
            SELECT
                LTRIM(RTRIM(ai.H6_FILIAL)) AS branch,
                LTRIM(RTRIM(ai.H6_PRODUTO)) AS product_code,
                LTRIM(RTRIM(ai.B1_TIPO)) AS product_type,
                MAX(LTRIM(RTRIM(SB1.B1_DESC))) AS description,
                MAX(LTRIM(RTRIM(SB1.B1_UM))) AS unit,
                SUM(ai.qtd_produzida_op) AS produced_milheiro,
                SUM(ai.qtd_produzida_op) * 1000 AS produced_un,
                COUNT(DISTINCT ai.H6_OP) AS orders_count
            FROM apont_inspecao ai
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = ai.H6_PRODUTO
               AND SB1.D_E_L_E_T_ = ' '
            GROUP BY
                ai.H6_FILIAL,
                ai.H6_PRODUTO,
                ai.B1_TIPO
            ORDER BY
                ai.H6_FILIAL,
                ai.H6_PRODUTO
        """

        with self as repo:
            rows = repo.execute_query(sql, params) or []

        items = [
            ProducedQuantityItem(
                branch=str(row.get("branch") or "").strip(),
                product_code=str(row.get("product_code") or "").strip(),
                product_type=str(row.get("product_type") or "").strip(),
                description=str(row.get("description") or "").strip(),
                unit=str(row.get("unit") or "").strip(),
                produced_milheiro=float(row.get("produced_milheiro") or 0),
                produced_un=float(row.get("produced_un") or 0),
                orders_count=int(row.get("orders_count") or 0),
            )
            for row in rows
        ]

        by_product = self._aggregate_produced_by_product(items)
        total_milheiro = sum(item.produced_milheiro for item in items)

        return ProducedQuantityReport(
            branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
            products=request.products,
            items=items,
            total_produced_milheiro=total_milheiro,
            total_produced_un=total_milheiro * 1000,
            by_product=by_product,
        )

    @staticmethod
    def _aggregate_produced_by_product(
        items: list[ProducedQuantityItem],
    ) -> list[ProducedQuantityByProduct]:
        by_product_map: dict[str, ProducedQuantityByProduct] = {}
        for item in items:
            existing = by_product_map.get(item.product_code)
            if existing is None:
                by_product_map[item.product_code] = ProducedQuantityByProduct(
                    product_code=item.product_code,
                    product_type=item.product_type,
                    description=item.description,
                    unit=item.unit,
                    produced_milheiro=item.produced_milheiro,
                    produced_un=item.produced_un,
                    orders_count=item.orders_count,
                    branches=[item.branch] if item.branch else [],
                )
                continue

            existing.produced_milheiro += item.produced_milheiro
            existing.produced_un += item.produced_un
            existing.orders_count += item.orders_count
            if item.branch and item.branch not in existing.branches:
                existing.branches.append(item.branch)

        return sorted(by_product_map.values(), key=lambda row: row.product_code)

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        date_start_protheus, date_end_exclusive = self._resolve_date_range(
            date_start,
            date_end,
        )

        where_nc, params_nc = build_nc_where_clause(
            ppm_type=ppm_type,
            branch=None,
            date_start=date_start_protheus,
            date_end_exclusive=date_end_exclusive,
        )
        where_nc = f"{where_nc} AND NULLIF(LTRIM(RTRIM(QI2_FILIAL)), '') IS NOT NULL"

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
                FROM QI2010 WITH (NOLOCK)
                WHERE {where_nc}

                UNION

                SELECT
                    LTRIM(RTRIM(H6_FILIAL)) AS branch
                FROM SH6010
                WHERE {' AND '.join(prod_filters)}
            ) branches
            WHERE branch <> ''
            ORDER BY branch
        """

        params = tuple(list(params_nc) + prod_params)

        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            str(row.get("branch")).strip()
            for row in rows
            if row.get("branch") and str(row.get("branch")).strip()
        ]

    def list_items(self, request) -> Page[PpmItem]:
        date_start, date_end_exclusive = self._resolve_date_range(
            request.date_start,
            request.date_end,
        )

        where_clause, params = build_nc_where_clause(
            ppm_type=request.type,
            branch=request.branch,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
        )

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
                    nc.QI2_FILIAL AS branch,
                    FORMAT(TRY_CONVERT(date, nc.QI2_OCORRE, 112), 'dd/MM/yyyy') AS registered_date,
                    nc.QI2_FNC AS code,
                    nc.QI2_REV AS revision,
                    nc.QI2_TIPO AS ppm_type,
                    CASE
                        WHEN nc.QI2_TIPO = '1' THEN 'interno'
                        WHEN nc.QI2_TIPO = '2' THEN 'externo_cliente'
                        WHEN nc.QI2_TIPO = '3' THEN 'fornecedor'
                        ELSE 'outro'
                    END AS ppm_type_description,
                    nc.QI2_ITEM AS item_code,
                    nc.QI2_DESCR AS description,
                    {qi2_detailed_description_sql(table_alias="nc")},
                    NULLIF(LTRIM(RTRIM(nc.QI2_CODCLI)), '') AS customer_code,
                    NULLIF(LTRIM(RTRIM(nc.QI2_LOJCLI)), '') AS customer_store,
                    NULLIF(LTRIM(RTRIM(SA1.A1_NOME)), '') AS customer_name,
                    nc.QI2_QTDDEV AS returned_quantity_original,
                    CAST(
                        COALESCE(
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(nc.QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                            TRY_PARSE(NULLIF(LTRIM(RTRIM(nc.QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
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
                    ORDER BY nc.QI2_OCORRE DESC, nc.QI2_FNC DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """

                final_params = list(params)
                final_params.extend([offset, request.page_size])
            else:
                page = 1

                sql = f"""
                    {select_sql}
                    ORDER BY nc.QI2_OCORRE DESC, nc.QI2_FNC DESC
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
