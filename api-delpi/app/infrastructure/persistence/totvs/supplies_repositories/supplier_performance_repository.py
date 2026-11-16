from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_sql import (
    MAX_SOURCE_ROWS,
    build_supplier_performance_sql,
)


class SupplierPerformanceRepository(BaseRepository):
    def read_counts(self, *, branches, date_from, date_to):
        sql, params = build_supplier_performance_sql(branches, date_from, date_to)
        with self as repo:
            rows = repo.execute_query(sql, params)
        if len(rows) > MAX_SOURCE_ROWS:
            raise ValueError(
                "A consulta excede o limite de fornecedores. Reduza o período ou selecione uma filial."
            )
        return rows
