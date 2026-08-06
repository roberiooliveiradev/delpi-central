from app.application.use_cases.process_inspection_plans.get_process_inspection_plans_product_use_case import (
    GetProcessInspectionPlansProductUseCase,
)
from app.application.use_cases.process_inspection_plans.get_process_inspection_plans_summary_use_case import (
    GetProcessInspectionPlansSummaryUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_orders_without_plan_use_case import (
    ListProcessInspectionPlansOrdersWithoutPlanUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_use_case import (
    ListProcessInspectionPlansProductsUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_without_plan_use_case import (
    ListProcessInspectionPlansProductsWithoutPlanUseCase,
)
from app.infrastructure.persistence.totvs.process_inspection_plans.process_inspection_plans_repository import (
    ProcessInspectionPlansRepository,
)
from app.infrastructure.persistence.totvs.product_repositories.product_inspection_repository import (
    ProductInspectionRepository,
)


def build_get_process_inspection_plans_summary_use_case() -> (
    GetProcessInspectionPlansSummaryUseCase
):
    return GetProcessInspectionPlansSummaryUseCase(
        repository=ProcessInspectionPlansRepository(),
    )


def build_list_process_inspection_plans_orders_without_plan_use_case() -> (
    ListProcessInspectionPlansOrdersWithoutPlanUseCase
):
    return ListProcessInspectionPlansOrdersWithoutPlanUseCase(
        repository=ProcessInspectionPlansRepository(),
    )


def build_list_process_inspection_plans_products_without_plan_use_case() -> (
    ListProcessInspectionPlansProductsWithoutPlanUseCase
):
    return ListProcessInspectionPlansProductsWithoutPlanUseCase(
        repository=ProcessInspectionPlansRepository(),
    )


def build_list_process_inspection_plans_products_use_case() -> (
    ListProcessInspectionPlansProductsUseCase
):
    return ListProcessInspectionPlansProductsUseCase(
        repository=ProcessInspectionPlansRepository(),
    )


def build_get_process_inspection_plans_product_use_case() -> (
    GetProcessInspectionPlansProductUseCase
):
    return GetProcessInspectionPlansProductUseCase(
        plans_repository=ProcessInspectionPlansRepository(),
        inspection_repository=ProductInspectionRepository(),
    )
