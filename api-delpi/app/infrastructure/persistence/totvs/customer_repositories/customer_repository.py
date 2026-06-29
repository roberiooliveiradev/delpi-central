from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.ports.customer.customer_query_repository_port import CustomerQueryRepositoryPort
from app.domain.entities.customer.customer_master import CustomerMaster
from app.application.models.page import Page
from app.infrastructure.persistence.totvs.pagination import paginate


class CustomerRepository(BaseRepository, CustomerQueryRepositoryPort):
    def search_customers(
        self,
        *,
        code: str | None = None,
        name: str | None = None,
        store: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[CustomerMaster]:
        paging = paginate(page, page_size)

        where_clauses = ["SA1.D_E_L_E_T_ = ''"]
        where_params: list[str] = []

        if code and code.strip():
            where_clauses.append("SA1.A1_COD LIKE ?")
            where_params.append(f"{code.strip()}%")

        if store and store.strip():
            where_clauses.append("SA1.A1_LOJA LIKE ?")
            where_params.append(f"{store.strip()}%")

        if name and name.strip():
            where_clauses.append("SA1.A1_NOME COLLATE Latin1_General_CI_AI LIKE ?")
            where_params.append(f"%{name.strip()}%")

        if len(where_clauses) == 1:
            where_clauses.append("SA1.A1_MSBLQL <> '1'")

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*) AS total
              FROM SA1010 SA1
             WHERE {where_sql}
        """

        sql = f"""
            SELECT
                SA1.A1_COD AS code,
                SA1.A1_LOJA AS store,
                SA1.A1_NOME AS name,
                SA1.A1_MSBLQL AS blocked
              FROM SA1010 SA1
             WHERE {where_sql}
             ORDER BY SA1.A1_NOME, SA1.A1_COD, SA1.A1_LOJA
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            total_row = repo.execute_one(count_sql, tuple(where_params))
            total = int(total_row["total"]) if total_row else 0
            rows = repo.execute_query(
                sql,
                tuple(where_params + [paging["offset"], paging["page_size"]]),
            )

        items = [
            CustomerMaster(
                code=(row.get("code") or "").strip(),
                store=(row.get("store") or "").strip(),
                name=(row.get("name") or "").strip(),
                blocked=row.get("blocked"),
            )
            for row in rows
        ]

        return Page(
            items=items,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )
