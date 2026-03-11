# app/infrastructure/persistence/totvs/product_repositories/product_repository.py

from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.entities.product import Product
from app.application.models.page import Page
from app.infrastructure.persistence.pagination import paginate
from app.domain.ports.product_query_repository_port import ProductQueryRepositoryPort


class ProductRepository(BaseRepository, ProductQueryRepositoryPort):

    def search_products(
        self,
        code=None,
        group=None,
        description=None,
        page=1,
        page_size=50,
        sort=None,
        direction="asc"
    ) -> Page[Product]:

        paging = paginate(page, page_size)

        where_clauses = ["SB1.D_E_L_E_T_ = ''"]
        where_params = []

        # -----------------------------
        # CODE
        # -----------------------------

        if code:
            where_clauses.append("SB1.B1_COD LIKE ?")
            where_params.append(f"{code}%")

        # -----------------------------
        # GROUP
        # -----------------------------

        if group:
            where_clauses.append("SB1.B1_GRUPO = ?")
            where_params.append(group)

        # -----------------------------
        # DESCRIPTION SEARCH
        # -----------------------------

        score_sql = "0"
        score_params = []

        if description:

            desc_clean = description.strip()
            terms = [t for t in desc_clean.split() if t]

            desc_where = []

            for t in terms:
                desc_where.append(
                    "SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?"
                )
                where_params.append(f"{t}%")

            where_clauses.append("(" + " OR ".join(desc_where) + ")")

            score_parts = []

            score_parts.append(
                "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 100 ELSE 0 END"
            )
            score_params.append(f"{desc_clean}%")

            for t in terms:
                score_parts.append(
                    "CASE WHEN SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ? THEN 20 ELSE 0 END"
                )
                score_params.append(f"{t}%")

            score_sql = " + ".join(score_parts)

        where_clause = " AND ".join(where_clauses)

        # -----------------------------
        # SORT
        # -----------------------------

        sortable_fields = {
            "code": "SB1.B1_COD",
            "description": "SB1.B1_DESC",
            "group_code": "SB1.B1_GRUPO"
        }

        sort_column = sortable_fields.get(sort, None)

        direction = "DESC" if str(direction).lower() == "desc" else "ASC"

        if sort_column:
            order_clause = f"{sort_column} {direction}"
        else:
            order_clause = "relevance_score DESC, SB1.B1_DESC, SB1.B1_COD"

        # -----------------------------
        # COUNT
        # -----------------------------

        count_sql = f"""
        SELECT COUNT(*) as total
        FROM SB1010 SB1
        WHERE {where_clause}
        """

        # -----------------------------
        # DATA
        # -----------------------------

        sql = f"""
        SELECT
            SB1.B1_COD AS code,
            SB1.B1_DESC AS description,
            SB1.B1_GRUPO AS group_code,
            ({score_sql}) AS relevance_score
        FROM SB1010 SB1
        WHERE {where_clause}
        ORDER BY {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                tuple(where_params)
            )

            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                sql,
                tuple(score_params + where_params + [paging["offset"], paging["page_size"]])
            )

        products = [
            Product(
                code=row["code"],
                description=row["description"],
                group_code=row["group_code"]
            )
            for row in rows
        ]

        return Page(
            items=products,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"]
        )