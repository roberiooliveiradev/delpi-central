import os

from app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from app.application.use_cases.kaizen.get_kaizen_summary_use_case import (
    GetKaizenSummaryUseCase,
)
from app.application.use_cases.nonconformity.list_nonconformity_use_case import (
    ListNonconformityUseCase,
)
from app.application.use_cases.ppm.get_ppm_summary_use_case import (
    GetPpmSummaryUseCase,
)
from app.application.use_cases.ppm.list_ppm_use_case import (
    ListPpmUseCase,
)
from app.infrastructure.persistence.google_sheets.audit_5s.audit_5s_repository import (
    Audit5SRepository,
)
from app.infrastructure.persistence.google_sheets.kaizen.kaizen_repository import (
    KaizenRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_query_repository import (
    NonconformityQueryRepository,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)

DEFAULT_QUALITY_SHEET_ID = "1e7RWYCcxsD8oem4aqjSzPYPYu9GuBDjZrb5Xd-fQ0tQ"
DEFAULT_KAIZEN_SHEET_GID = "1320135691"
DEFAULT_AUDIT_5S_SHEET_GID = "1189329906"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_google_sheets_client() -> GoogleSheetsClient:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    return GoogleSheetsClient(timeout=timeout)


def _build_utils() -> Utils:
    return Utils()


def _build_quality_sheet_id() -> str:
    return os.getenv("QUALITY_SHEET_ID", DEFAULT_QUALITY_SHEET_ID)


def _build_kaizen_repository() -> KaizenRepository:
    return KaizenRepository(
        client=_build_google_sheets_client(),
        sheet_id=_build_quality_sheet_id(),
        gid=os.getenv("QUALITY_KAIZEN_SHEET_GID", DEFAULT_KAIZEN_SHEET_GID),
        utils=_build_utils(),
    )


def _build_audit_5s_repository() -> Audit5SRepository:
    return Audit5SRepository(
        client=_build_google_sheets_client(),
        sheet_id=_build_quality_sheet_id(),
        gid=os.getenv("QUALITY_AUDIT_5S_SHEET_GID", DEFAULT_AUDIT_5S_SHEET_GID),
        utils=_build_utils(),
    )


def _build_ppm_repository() -> PpmQueryRepository:
    return PpmQueryRepository()


def _build_nonconformity_repository() -> NonconformityQueryRepository:
    return NonconformityQueryRepository()


def build_get_kaizen_summary_use_case() -> GetKaizenSummaryUseCase:
    return GetKaizenSummaryUseCase(repository=_build_kaizen_repository())


def build_get_audit_5s_summary_use_case() -> GetAudit5SSummaryUseCase:
    return GetAudit5SSummaryUseCase(repository=_build_audit_5s_repository())


def build_get_ppm_summary_use_case() -> GetPpmSummaryUseCase:
    return GetPpmSummaryUseCase(_build_ppm_repository())


def build_list_ppm_use_case() -> ListPpmUseCase:
    return ListPpmUseCase(_build_ppm_repository())


def build_list_nonconformity_use_case() -> ListNonconformityUseCase:
    return ListNonconformityUseCase(_build_nonconformity_repository())


def build_quality_metrics_snapshot_service() -> QualityMetricsSnapshotService:
    return QualityMetricsSnapshotService(
        internal_ppm_use_case=build_get_ppm_summary_use_case(),
        external_ppm_use_case=build_get_ppm_summary_use_case(),
        kaizen_summary_use_case=build_get_kaizen_summary_use_case(),
        audit_5s_summary_use_case=build_get_audit_5s_summary_use_case(),
    )


def build_get_quality_indicators_snapshot_port() -> QualityIndicatorsSnapshotProvider:
    return QualityIndicatorsSnapshotProvider(
        quality_metrics_snapshot_service=build_quality_metrics_snapshot_service(),
    )