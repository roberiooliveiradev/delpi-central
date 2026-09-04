from app.application.use_cases.commercial.get_segment_rol_target_use_case import (
    GetSegmentRolTargetUseCase,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository
from app.application.use_cases.commercial.get_sales_conversion_rate_use_case import GetSalesConversionRateUseCase
from app.application.use_cases.commercial.get_sales_conversion_rate_series_use_case import (
    GetSalesConversionRateSeriesUseCase,
)
from app.application.use_cases.commercial.get_sales_conversion_rate_series_use_case import (
    GetSalesConversionRateSeriesUseCase,
)
from app.application.use_cases.commercial.get_commercial_proposal_use_case import (
    GetCommercialProposalUseCase,
)
from app.application.use_cases.commercial.list_commercial_proposals_use_case import (
    ListCommercialProposalsUseCase,
)
from app.application.use_cases.commercial.summarize_commercial_proposals_by_collaborator_use_case import (
    SummarizeCommercialProposalsByCollaboratorUseCase,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import (
    CommercialProposalsRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import SalesConversionRateRepository
from app.application.use_cases.commercial.get_new_clients_average_use_case import GetNewClientsAverageUseCase
from app.infrastructure.persistence.totvs.commercial_repositories.new_clients_average_repository import NewClientsAverageRepository
from app.application.use_cases.commercial.get_new_clients_rol_pct_use_case import GetNewClientsRolPctUseCase
from app.application.use_cases.commercial.get_commercial_rol_series_use_case import (
    GetCommercialRolSeriesUseCase,
)
from app.application.use_cases.commercial.get_commercial_rol_by_customer_use_case import (
    GetCommercialRolByCustomerUseCase,
)
from app.application.use_cases.commercial.get_commercial_rol_by_product_use_case import (
    GetCommercialRolByProductUseCase,
)
from app.application.use_cases.commercial.get_commercial_rol_by_branch_use_case import (
    GetCommercialRolByBranchUseCase,
)
from app.application.use_cases.commercial.get_commercial_rol_summary_use_case import (
    GetCommercialRolSummaryUseCase,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_rol_by_customer_repository import (
    CommercialRolByCustomerRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_rol_by_product_repository import (
    CommercialRolByProductRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.new_clients_rol_pct_repository import NewClientsRolPctRepository
from app.application.use_cases.commercial.get_new_business_rol_pct_use_case import (
    GetNewBusinessRolPctUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_use_case import GetSalesOrderOtdUseCase
from app.application.use_cases.commercial.get_sales_order_otd_panel_use_case import (
    GetSalesOrderOtdPanelUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_series_use_case import (
    GetSalesOrderOtdSeriesUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_line_detail_use_case import (
    GetSalesOrderOtdLineDetailUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_by_customer_use_case import (
    GetSalesOrderOtdByCustomerUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_by_branch_use_case import (
    GetSalesOrderOtdByBranchUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_series_by_customer_use_case import (
    GetSalesOrderOtdSeriesByCustomerUseCase,
)
from app.infrastructure.persistence.totvs.commercial_repositories.new_business_rol_pct_repository import (
    NewBusinessRolPctRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)
def build_get_sales_conversion_rate_use_case() -> GetSalesConversionRateUseCase:
    return GetSalesConversionRateUseCase(
        sales_conversion_rate_repository=SalesConversionRateRepository()
    )


def build_get_sales_conversion_rate_series_use_case() -> GetSalesConversionRateSeriesUseCase:
    return GetSalesConversionRateSeriesUseCase(
        sales_conversion_rate_repository=SalesConversionRateRepository()
    )


def build_list_commercial_proposals_use_case() -> ListCommercialProposalsUseCase:
    return ListCommercialProposalsUseCase(
        commercial_proposals_repository=CommercialProposalsRepository()
    )


def build_summarize_commercial_proposals_by_collaborator_use_case() -> SummarizeCommercialProposalsByCollaboratorUseCase:
    return SummarizeCommercialProposalsByCollaboratorUseCase(
        commercial_proposals_repository=CommercialProposalsRepository()
    )


def build_get_commercial_proposal_use_case() -> GetCommercialProposalUseCase:
    return GetCommercialProposalUseCase(
        commercial_proposals_repository=CommercialProposalsRepository(),
        lmp_query_repository=LMPQueryRepository(),
    )


def build_get_new_clients_average_use_case() -> GetNewClientsAverageUseCase:
    return GetNewClientsAverageUseCase(
        new_clients_average_repository=NewClientsAverageRepository()
    )


def build_get_new_clients_rol_pct_use_case() -> GetNewClientsRolPctUseCase:
    return GetNewClientsRolPctUseCase(
        new_clients_rol_pct_repository=NewClientsRolPctRepository()
    )


def build_get_commercial_rol_series_use_case() -> GetCommercialRolSeriesUseCase:
    return GetCommercialRolSeriesUseCase(
        financial_query_repository=FinancialRepository()
    )


def build_get_commercial_rol_by_customer_use_case() -> GetCommercialRolByCustomerUseCase:
    return GetCommercialRolByCustomerUseCase(
        repository=CommercialRolByCustomerRepository()
    )


def build_get_commercial_rol_by_product_use_case() -> GetCommercialRolByProductUseCase:
    return GetCommercialRolByProductUseCase(
        repository=CommercialRolByProductRepository()
    )


def build_get_commercial_rol_by_branch_use_case() -> GetCommercialRolByBranchUseCase:
    return GetCommercialRolByBranchUseCase(
        financial_query_repository=FinancialRepository()
    )


def build_get_commercial_rol_summary_use_case() -> GetCommercialRolSummaryUseCase:
    return GetCommercialRolSummaryUseCase(
        financial_query_repository=FinancialRepository()
    )


def build_get_sales_order_otd_use_case() -> GetSalesOrderOtdUseCase:
    return GetSalesOrderOtdUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_by_customer_use_case() -> GetSalesOrderOtdByCustomerUseCase:
    return GetSalesOrderOtdByCustomerUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_by_branch_use_case() -> GetSalesOrderOtdByBranchUseCase:
    return GetSalesOrderOtdByBranchUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_panel_use_case() -> GetSalesOrderOtdPanelUseCase:
    return GetSalesOrderOtdPanelUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_series_use_case() -> GetSalesOrderOtdSeriesUseCase:
    return GetSalesOrderOtdSeriesUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_series_by_customer_use_case() -> (
    GetSalesOrderOtdSeriesByCustomerUseCase
):
    return GetSalesOrderOtdSeriesByCustomerUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_sales_order_otd_line_detail_use_case() -> GetSalesOrderOtdLineDetailUseCase:
    return GetSalesOrderOtdLineDetailUseCase(
        sales_order_otd_repository=SalesOrderOtdRepository()
    )


def build_get_new_business_rol_pct_use_case() -> GetNewBusinessRolPctUseCase:
    return GetNewBusinessRolPctUseCase(
        new_business_rol_pct_repository=NewBusinessRolPctRepository()
    )


def _build_segment_rol_target_use_case(
    *,
    segment_kind: str,
) -> GetSegmentRolTargetUseCase:
    return GetSegmentRolTargetUseCase(
        new_business_rol_pct_repository=NewBusinessRolPctRepository(),
        segment_kind=segment_kind,  # type: ignore[arg-type]
    )


def build_get_weg_rol_target_use_case() -> GetSegmentRolTargetUseCase:
    return _build_segment_rol_target_use_case(segment_kind="weg")


def build_get_new_business_rol_target_use_case() -> GetSegmentRolTargetUseCase:
    return _build_segment_rol_target_use_case(segment_kind="new_business")