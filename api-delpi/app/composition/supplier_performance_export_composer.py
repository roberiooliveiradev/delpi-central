from app.application.use_cases.supplies.get_supplier_performance_export_use_case import (
    GetSupplierPerformanceExportUseCase,
)
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_export_repository import (
    SupplierPerformanceExportRepository,
)


def build_supplier_performance_export_use_case():
    return GetSupplierPerformanceExportUseCase(SupplierPerformanceExportRepository())
