from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from si_app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from si_app.application.use_cases.kaizen.get_kaizen_summary_use_case import (
    GetKaizenSummaryUseCase,
)
from si_app.application.use_cases.ppm.get_ppm_summary_use_case import (
    GetPpmSummaryUseCase,
)
from si_app.infrastructure.gateways.delpi_quality_gateway import (
    DelpiAudit5SGateway,
    DelpiKaizenGateway,
    DelpiPpmGateway,
)
from si_app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def _build_ppm_gateway() -> DelpiPpmGateway:
    return DelpiPpmGateway(_get_delpi_client())


def _build_kaizen_gateway() -> DelpiKaizenGateway:
    return DelpiKaizenGateway(_get_delpi_client())


def _build_audit_5s_gateway() -> DelpiAudit5SGateway:
    return DelpiAudit5SGateway(_get_delpi_client())


def build_get_kaizen_summary_use_case() -> GetKaizenSummaryUseCase:
    return GetKaizenSummaryUseCase(repository=_build_kaizen_gateway())


def build_get_audit_5s_summary_use_case() -> GetAudit5SSummaryUseCase:
    return GetAudit5SSummaryUseCase(repository=_build_audit_5s_gateway())


def build_get_ppm_summary_use_case() -> GetPpmSummaryUseCase:
    return GetPpmSummaryUseCase(_build_ppm_gateway())


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
