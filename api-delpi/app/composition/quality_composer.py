from app.config import settings

from app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from app.application.use_cases.kaizen.get_kaizen_summary_use_case import (
    GetKaizenSummaryUseCase,
)
from app.application.use_cases.nonconformity.get_nonconformity_series_use_case import (
    GetNonconformitySeriesUseCase,
)
from app.application.use_cases.nonconformity.list_nonconformity_use_case import (
    ListNonconformityUseCase,
)
from app.application.use_cases.ppm.get_ppm_series_use_case import (
    GetPpmSeriesUseCase,
)
from app.application.use_cases.ppm.get_ppm_summary_use_case import (
    GetPpmSummaryUseCase,
)
from app.application.use_cases.ppm.list_ppm_use_case import (
    ListPpmUseCase,
)
from app.application.use_cases.quality.list_quality_branches_use_case import (
    ListQualityBranchesUseCase,
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
def _build_google_sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT))


def _build_utils() -> Utils:
    return Utils()


def _build_kaizen_repository() -> KaizenRepository:
    return KaizenRepository(
        client=_build_google_sheets_client(),
        sheet_id=settings.QUALITY_SHEET_ID,
        gid=settings.QUALITY_KAIZEN_SHEET_GID,
        utils=_build_utils(),
    )


def _build_audit_5s_repository() -> Audit5SRepository:
    return Audit5SRepository(
        client=_build_google_sheets_client(),
        sheet_id=settings.QUALITY_SHEET_ID,
        gid=settings.QUALITY_AUDIT_5S_SHEET_GID,
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


def build_get_ppm_series_use_case() -> GetPpmSeriesUseCase:
    return GetPpmSeriesUseCase(_build_ppm_repository())


def build_list_quality_branches_use_case() -> ListQualityBranchesUseCase:
    return ListQualityBranchesUseCase(_build_ppm_repository())


def build_list_nonconformity_use_case() -> ListNonconformityUseCase:
    return ListNonconformityUseCase(_build_nonconformity_repository())


def build_get_nonconformity_series_use_case() -> GetNonconformitySeriesUseCase:
    return GetNonconformitySeriesUseCase(_build_nonconformity_repository())


def build_quality_metrics_snapshot_service() -> QualityMetricsSnapshotService:
    return QualityMetricsSnapshotService(
        internal_ppm_use_case=build_get_ppm_summary_use_case(),
        external_ppm_use_case=build_get_ppm_summary_use_case(),
        kaizen_summary_use_case=build_get_kaizen_summary_use_case(),
        audit_5s_summary_use_case=build_get_audit_5s_summary_use_case(),
    )

