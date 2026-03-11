# app/infrastructure/persistence/totvs/product_repositories/product_repository.py

from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.entities.product import Product
from app.application.models.page import Page
from app.infrastructure.persistence.query_builder import QueryBuilder
from app.infrastructure.persistence.pagination import paginate
from app.domain.ports.product_query_repository_port import ProductQueryRepositoryPort


class ProductRepository(BaseRepository, ProductQueryRepositoryPort):

    def search_products(
        self,
        code=None,
        group=None,
        description=None,
        page=1,
        page_size=50
    ) -> Page[Product]:

        qb = QueryBuilder()

        qb.raw("SB1.D_E_L_E_T_ = ''")
        qb.like("SB1.B1_COD", code)
        qb.like("SB1.B1_GRUPO", group)
        qb.like("SB1.B1_DESC COLLATE Latin1_General_CI_AI", description)

        where_clause, params = qb.build()

        paging = paginate(page, page_size)

        count_sql = f"""
        SELECT COUNT(*) as total
        FROM SB1010 SB1
        WHERE {where_clause}
        """

        sql = f"""
        SELECT
            SB1.B1_COD AS code,
            SB1.B1_DESC AS description,
            SB1.B1_GRUPO AS group_code
        FROM SB1010 SB1
        WHERE {where_clause}
        ORDER BY SB1.B1_COD
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(count_sql, tuple(params))
            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                sql,
                tuple(params + [paging["offset"], paging["page_size"]])
            )

        products = [
            Product(**row)
            for row in rows
        ]

        return Page(
            items=products,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"]
        )
    
