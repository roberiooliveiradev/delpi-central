# app/infrastructure/persistence/totvs/sale_orders_repositories/sale_orders_query_repository.py
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.entities.sale.sale_order import SaleOrder
from app.application.dto.sale_order.list_sale_order_request import ListSaleOrderRequest
from app.domain.ports.sale.sale_order_query_repository_port import SaleOrderQueryRepositoryPort
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.models.page import Page


class SaleQueryRepository(BaseRepository, SaleOrderQueryRepositoryPort):

    def list_sales_orders(
        self,
        request: ListSaleOrderRequest
    ) -> Page[SaleOrder]:

        qb = QueryBuilder()

        qb.raw("D_E_L_E_T_ = ''")
        qb.date_range(
            field="AD1_DATA",
            start=request.date_start,
            end=request.date_end
        )

        where_clause, params = qb.build()

        base_sql = f"""
            FROM AD1010
            WHERE {where_clause}
        """

        with self as repo:

            # -------------------------------------------------
            # TOTAL
            # -------------------------------------------------

            total_sql = f"""
                SELECT COUNT(1)
                {base_sql}
            """

            total = repo.execute_scalar(total_sql, params)

            # -------------------------------------------------
            # PAGINAÇÃO
            # -------------------------------------------------

            if request.page_size:

                page = request.page or 1
                offset = (page - 1) * request.page_size

                sql = f"""
                    SELECT
                        AD1_FILIAL as branch,
                        AD1_NROPOR as order_number,
                        AD1_REVISA as revision_number,
                        AD1_DESCRI as description,
                        AD1_DATA as date,
                        AD1_USER as user_code,
                        AD1_VEND as seller_code,
                        AD1_DTINI as start_date,
                        AD1_DTFIM as end_date,
                        AD1_CODCLI as costumer_code,
                        AD1_STAGE as stage,
                        AD1_CODPRO as product_code
                    {base_sql}
                    ORDER BY AD1_DATA DESC
                    OFFSET ? ROWS
                    FETCH NEXT ? ROWS ONLY
                """

                params = list(params)
                params.extend([offset, request.page_size])

            else:

                sql = f"""
                    SELECT
                        AD1_FILIAL as branch,
                        AD1_NROPOR as order_number,
                        AD1_REVISA as revision_number,
                        AD1_DESCRI as description,
                        AD1_DATA as date,
                        AD1_USER as user_code,
                        AD1_VEND as seller_code,
                        AD1_DTINI as start_date,
                        AD1_DTFIM as end_date,
                        AD1_CODCLI as costumer_code,
                        AD1_STAGE as stage,
                        AD1_CODPRO as product_code
                    {base_sql}
                    ORDER BY AD1_DATA DESC
                """

                page = 1

            rows = repo.execute_query(sql, params)

            items = [
                SaleOrder(**row)
                for row in rows
            ]

            return Page(
                items=items,
                total=total,
                page=page,
                page_size=request.page_size or total
            )