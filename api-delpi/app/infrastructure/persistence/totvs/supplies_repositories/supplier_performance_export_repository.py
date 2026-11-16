"""Read-only, bounded evidence behind the IDF XLSX report."""
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_export_sql import (
    MAX_EXPORT_ROWS_PER_SOURCE,
    build_delivery_evidence_sql,
    build_inspection_evidence_sql,
)


class SupplierPerformanceExportRepository(BaseRepository):
    def read_evidence(self, *, branches, date_from, date_to, supplier_code=None, supplier_store=None):
        inspections_sql, inspections_params = build_inspection_evidence_sql(
            branches, date_from, date_to, supplier_code, supplier_store
        )
        deliveries_sql, deliveries_params = build_delivery_evidence_sql(
            branches, date_from, date_to, supplier_code, supplier_store
        )
        with self as repo:
            inspections = repo.execute_query(inspections_sql, inspections_params)
            if len(inspections) > MAX_EXPORT_ROWS_PER_SOURCE:
                raise ValueError(
                    "Há mais de 12.000 inspeções no recorte. Escolha um fornecedor ou reduza o período."
                )
            deliveries = repo.execute_query(deliveries_sql, deliveries_params)
            if len(deliveries) > MAX_EXPORT_ROWS_PER_SOURCE:
                raise ValueError(
                    "Há mais de 12.000 recebimentos no recorte. Escolha um fornecedor ou reduza o período."
                )
        return inspections, deliveries
