from si_app.config import settings

from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from si_app.application.use_cases.financial.get_rol_use_case import GetRolUseCase
from si_app.infrastructure.persistence.google_sheets.financial.financial_ebitda_repository import (
    FinancialEbitdaRepository,
)
from si_app.infrastructure.persistence.google_sheets.financial.financial_fixed_cost_repository import (
    FinancialFixedCostRepository,
)
from si_app.infrastructure.persistence.google_sheets.financial.financial_receivables_repository import (
    FinancialReceivablesRepository,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from delpi_api_client import DelpiApiClient
from si_app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from si_app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)

from si_app.application.use_cases.financial.get_financial_ebitda_pct_use_case import (
    GetFinancialEbitdaPctUseCase,
)
from si_app.application.use_cases.financial.get_financial_fixed_cost_pct_use_case import (
    GetFinancialFixedCostPctUseCase,
)
from si_app.application.use_cases.financial.get_financial_pmr_use_case import (
    GetFinancialPmrUseCase,
)


def _build_google_sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT))


def _build_financial_ebitda_repository(
    client: GoogleSheetsClient,
) -> FinancialEbitdaRepository:
    return FinancialEbitdaRepository(
        client=client,
        sheet_id=settings.FINANCIAL_EBITDA_SHEET_ID,
        gid=settings.FINANCIAL_EBITDA_SHEET_GID,
    )


def _build_financial_fixed_cost_repository(
    client: GoogleSheetsClient,
) -> FinancialFixedCostRepository:
    return FinancialFixedCostRepository(
        client=client,
        sheet_id=settings.FINANCIAL_FIXED_COST_SHEET_ID,
        gid=settings.FINANCIAL_FIXED_COST_SHEET_GID,
    )


def _build_financial_receivables_repository(
    client: GoogleSheetsClient,
) -> FinancialReceivablesRepository:
    return FinancialReceivablesRepository(
        client=client,
        sheet_id=settings.FINANCIAL_RECEIVABLES_SHEET_ID,
        gid=settings.FINANCIAL_RECEIVABLES_SHEET_GID,
    )


def _build_delpi_financial_gateway() -> DelpiFinancialGateway:
    return DelpiFinancialGateway(DelpiApiClient())


def build_financial_metrics_snapshot_service() -> FinancialMetricsSnapshotService:
    client = _build_google_sheets_client()

    return FinancialMetricsSnapshotService(
        ebitda_repository=_build_financial_ebitda_repository(client),
        fixed_cost_repository=_build_financial_fixed_cost_repository(client),
        receivables_repository=_build_financial_receivables_repository(client),
        financial_query_repository=_build_delpi_financial_gateway(),
    )


def build_get_financial_indicators_snapshot_port() -> FinancialIndicatorsSnapshotProvider:
    return FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )


def build_get_rol_use_case() -> GetRolUseCase:
    return GetRolUseCase(_build_delpi_financial_gateway())


def build_get_financial_ebitda_pct_use_case() -> GetFinancialEbitdaPctUseCase:
    return GetFinancialEbitdaPctUseCase(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )


def build_get_financial_fixed_cost_pct_use_case() -> GetFinancialFixedCostPctUseCase:
    return GetFinancialFixedCostPctUseCase(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )


def build_get_financial_pmr_use_case() -> GetFinancialPmrUseCase:
    return GetFinancialPmrUseCase(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )