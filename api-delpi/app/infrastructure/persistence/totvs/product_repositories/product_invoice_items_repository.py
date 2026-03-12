# app/infrastructure/persistence/totvs/product_repositories/product_invoice_items_repository.py

from typing import Optional

from app.infrastructure.persistence.base_repository import BaseRepository
from app.infrastructure.persistence.pagination import paginate
from app.infrastructure.persistence.query_builder import QueryBuilder

from app.application.models.page import Page
from app.domain.entities.inbound_invoice_item import InboundInvoiceItem
from app.domain.entities.outbound_invoice_item import OutboundInvoiceItem
from app.domain.ports.product_invoice_items_repository_port import ProductInvoiceItemsRepositoryPort


class ProductInvoiceItemsRepository(
    BaseRepository,
    ProductInvoiceItemsRepositoryPort
):

    # -------------------------------------------
    # INBOUND
    # -------------------------------------------

    def list_inbound_invoice_items(
        self,
        code: str,
        page: int,
        page_size: int,
        issue_date_start: Optional[str],
        issue_date_end: Optional[str],
        supplier: Optional[str],
        branch: Optional[str]
    ) -> Page[InboundInvoiceItem]:

        paging = paginate(page, page_size)

        qb = QueryBuilder()

        qb.raw("SD1.D_E_L_E_T_ = ''")
        qb.eq("SD1.D1_COD", code)
        qb.date_range("SD1.D1_EMISSAO", issue_date_start, issue_date_end)
        qb.eq("SD1.D1_FORNECE", supplier)
        qb.eq("SD1.D1_FILIAL", branch)

        where_clause, params = qb.build()

        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM SD1010 SD1
        WHERE {where_clause}
        """

        data_sql = f"""
        SELECT
            SD1.D1_FILIAL    AS branch,
            SD1.D1_DOC       AS invoice_number,
            SD1.D1_SERIE     AS invoice_series,
            SD1.D1_ITEM      AS item,
            SD1.D1_EMISSAO   AS issue_date,

            SD1.D1_COD       AS product_code,
            SB1.B1_DESC      AS product_description,
            SB1.B1_UM        AS unit,

            SD1.D1_FORNECE   AS supplier_code,
            SA2.A2_NOME      AS supplier_name,

            SD1.D1_QUANT     AS quantity,
            CASE 
                WHEN SD1.D1_QUANT <> 0 
                THEN SD1.D1_TOTAL / SD1.D1_QUANT 
                ELSE 0 
            END              AS unit_price,

            SD1.D1_TOTAL     AS total_value

        FROM SD1010 SD1

        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = SD1.D1_COD
            AND SB1.D_E_L_E_T_ = ''

        LEFT JOIN SA2010 SA2
            ON SA2.A2_COD = SD1.D1_FORNECE
            AND SA2.A2_LOJA = SD1.D1_LOJA
            AND SA2.D_E_L_E_T_ = ''

        WHERE {where_clause}

        ORDER BY SD1.D1_EMISSAO DESC

        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(count_sql, params)
            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                data_sql,
                params + (paging["offset"], paging["page_size"])
            )

        items = [InboundInvoiceItem(**r) for r in rows]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    # -------------------------------------------
    # OUTBOUND
    # -------------------------------------------

    def list_outbound_invoice_items(
        self,
        code: str,
        page: int,
        page_size: int,
        issue_date_start: Optional[str],
        issue_date_end: Optional[str],
        customer: Optional[str],
        branch: Optional[str]
    ) -> Page[OutboundInvoiceItem]:

        paging = paginate(page, page_size)

        qb = QueryBuilder()

        qb.raw("SD2.D_E_L_E_T_ = ''")
        qb.eq("SD2.D2_COD", code)
        qb.date_range("SD2.D2_EMISSAO", issue_date_start, issue_date_end)
        qb.eq("SD2.D2_CLIENTE", customer)
        qb.eq("SD2.D2_FILIAL", branch)

        where_clause, params = qb.build()

        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM SD2010 SD2
        WHERE {where_clause}
        """

        data_sql = f"""
        SELECT
            SD2.D2_FILIAL    AS branch,
            SD2.D2_DOC       AS invoice_number,
            SD2.D2_SERIE     AS invoice_series,
            SD2.D2_ITEM      AS item,
            SD2.D2_EMISSAO   AS issue_date,

            SD2.D2_COD       AS product_code,
            SB1.B1_DESC      AS product_description,
            SB1.B1_UM        AS unit,

            SD2.D2_CLIENTE   AS customer_code,
            SA1.A1_NOME      AS customer_name,

            SD2.D2_QUANT     AS quantity,
            SD2.D2_PRCVEN    AS unit_price,
            (SD2.D2_QUANT * SD2.D2_PRCVEN) AS total_value

        FROM SD2010 SD2

        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = SD2.D2_COD
            AND SB1.D_E_L_E_T_ = ''

        LEFT JOIN SA1010 SA1
            ON SA1.A1_COD = SD2.D2_CLIENTE
            AND SA1.A1_LOJA = SD2.D2_LOJA
            AND SA1.D_E_L_E_T_ = ''

        WHERE {where_clause}

        ORDER BY SD2.D2_EMISSAO DESC

        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(count_sql, params)
            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                data_sql,
                params + (paging["offset"], paging["page_size"])
            )

        items = [OutboundInvoiceItem(**r) for r in rows]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )