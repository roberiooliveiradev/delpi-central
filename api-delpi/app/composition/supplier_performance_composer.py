from app.application.use_cases.supplies.get_supplier_performance_use_case import (
    GetSupplierPerformanceUseCase,
)
from app.composition.query_cache_composer import build_query_cache
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_repository import (
    SupplierPerformanceRepository,
)


def build_supplier_performance_use_case():
    return GetSupplierPerformanceUseCase(
        SupplierPerformanceRepository(), build_query_cache()
    )
