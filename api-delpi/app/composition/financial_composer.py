# app/composition/financial_composer.py

import os

from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from app.application.use_cases.financial.get_rol_use_case import GetRolUseCase
from app.infrastructure.persistence.google_sheets.financial.financial_metrics_repository import (
    FinancialMetricsRepository,
)
from app.infrastructure.persistence.google_sheets.financial.sheet_sources import (
    FinancialIndicatorsSources,
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

DEFAULT_FINANCIAL_SHEET_ID = "1Esd2boUNbaHxwBsO1X_fEPITVNCOD3fxmY8z8D4K9Mg"
DEFAULT_FINANCIAL_GID_EBITDA = "1525246844"
DEFAULT_FINANCIAL_GID_FIXED_COST = "1959625411"
DEFAULT_FINANCIAL_GID_RECEIVABLES = "594516707"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_google_sheets_client() -> GoogleSheetsClient:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    return GoogleSheetsClient(timeout=timeout)


def _build_financial_sources() -> FinancialIndicatorsSources:
    sheet_id = os.getenv("FINANCIAL_SHEET_ID", DEFAULT_FINANCIAL_SHEET_ID)

    return FinancialIndicatorsSources(
        sheet_id=sheet_id,
        tabs={
            "ebitda": os.getenv(
                "FINANCIAL_GID_EBITDA",
                DEFAULT_FINANCIAL_GID_EBITDA,
            ),
            "fixed_cost": os.getenv(
                "FINANCIAL_GID_FIXED_COST",
                DEFAULT_FINANCIAL_GID_FIXED_COST,
            ),
            "receivables": os.getenv(
                "FINANCIAL_GID_RECEIVABLES",
                DEFAULT_FINANCIAL_GID_RECEIVABLES,
            ),
        },
    )


def build_financial_metrics_repository() -> FinancialMetricsRepository:
    return FinancialMetricsRepository(
        client=_build_google_sheets_client(),
        sources=_build_financial_sources(),
    )


def build_financial_metrics_snapshot_service() -> FinancialMetricsSnapshotService:
    return FinancialMetricsSnapshotService(
        sheets_repository=build_financial_metrics_repository(),
        financial_query_repository=FinancialRepository(),
    )


def build_get_financial_indicators_snapshot_port() -> FinancialIndicatorsSnapshotProvider:
    return FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )


def build_get_rol_use_case() -> GetRolUseCase:
    repository = FinancialRepository()
    return GetRolUseCase(repository)