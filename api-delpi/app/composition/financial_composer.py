import os

from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from app.application.use_cases.financial.get_rol_use_case import GetRolUseCase
from app.infrastructure.persistence.google_sheets.financial.financial_ebitda_repository import (
    FinancialEbitdaRepository,
)
from app.infrastructure.persistence.google_sheets.financial.financial_fixed_cost_repository import (
    FinancialFixedCostRepository,
)
from app.infrastructure.persistence.google_sheets.financial.financial_receivables_repository import (
    FinancialReceivablesRepository,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)

from app.application.use_cases.financial.get_financial_ebitda_pct_use_case import (
    GetFinancialEbitdaPctUseCase,
)
from app.application.use_cases.financial.get_financial_fixed_cost_pct_use_case import (
    GetFinancialFixedCostPctUseCase,
)
from app.application.use_cases.financial.get_financial_pmr_use_case import (
    GetFinancialPmrUseCase,
)

DEFAULT_FINANCIAL_SHEET_ID = "1Esd2boUNbaHxwBsO1X_fEPITVNCOD3fxmY8z8D4K9Mg"
DEFAULT_FINANCIAL_GID_EBITDA = "1525246844"
DEFAULT_FINANCIAL_GID_FIXED_COST = "1959625411"
DEFAULT_FINANCIAL_GID_RECEIVABLES = "594516707"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_google_sheets_client() -> GoogleSheetsClient:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    return GoogleSheetsClient(timeout=timeout)


def _build_financial_ebitda_repository(
    client: GoogleSheetsClient,
) -> FinancialEbitdaRepository:
    sheet_id = os.getenv("FINANCIAL_EBITDA_SHEET_ID", DEFAULT_FINANCIAL_SHEET_ID)
    gid = os.getenv("FINANCIAL_EBITDA_SHEET_GID", DEFAULT_FINANCIAL_GID_EBITDA)
    return FinancialEbitdaRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def _build_financial_fixed_cost_repository(
    client: GoogleSheetsClient,
) -> FinancialFixedCostRepository:
    sheet_id = os.getenv("FINANCIAL_FIXED_COST_SHEET_ID", DEFAULT_FINANCIAL_SHEET_ID)
    gid = os.getenv("FINANCIAL_FIXED_COST_SHEET_GID", DEFAULT_FINANCIAL_GID_FIXED_COST)
    return FinancialFixedCostRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def _build_financial_receivables_repository(
    client: GoogleSheetsClient,
) -> FinancialReceivablesRepository:
    sheet_id = os.getenv("FINANCIAL_RECEIVABLES_SHEET_ID", DEFAULT_FINANCIAL_SHEET_ID)
    gid = os.getenv("FINANCIAL_RECEIVABLES_SHEET_GID", DEFAULT_FINANCIAL_GID_RECEIVABLES)
    return FinancialReceivablesRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def build_financial_metrics_snapshot_service() -> FinancialMetricsSnapshotService:
    client = _build_google_sheets_client()

    return FinancialMetricsSnapshotService(
        ebitda_repository=_build_financial_ebitda_repository(client),
        fixed_cost_repository=_build_financial_fixed_cost_repository(client),
        receivables_repository=_build_financial_receivables_repository(client),
        financial_query_repository=FinancialRepository(),
    )


def build_get_financial_indicators_snapshot_port() -> FinancialIndicatorsSnapshotProvider:
    return FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )


def build_get_rol_use_case() -> GetRolUseCase:
    repository = FinancialRepository()
    return GetRolUseCase(repository)


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