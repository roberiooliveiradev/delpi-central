from __future__ import annotations

from si_app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)
from si_app.application.use_cases.lmp.get_lmp_use_case import GetLMPUseCase
from si_app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    ListLMPDashboardUseCase,
)
from si_app.application.use_cases.lmp.list_lmp_use_case import ListLMPUseCase
from si_app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)
from si_app.application.use_cases.transforma_mais.list_process_use_case import (
    ListProcessUseCase,
)
from si_app.application.use_cases.lmp.get_lmp_dashboard_summary_use_case import (
    GetLMPDashboardSummaryUseCase,
)
from si_app.infrastructure.gateways.transformometro_transforma_mais_gateway import (
    TransformometroTransformaMaisGateway,
)
from si_app.infrastructure.gateways.delpi_engineering_gateway import (
    DelpiLmpGateway,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def _build_lmp_gateway() -> DelpiLmpGateway:
    return DelpiLmpGateway(_get_delpi_client())


def _build_transforma_mais_gateway() -> TransformometroTransformaMaisGateway:
    return TransformometroTransformaMaisGateway()


def build_engineering_list_lmps_use_case() -> ListLMPUseCase:
    return ListLMPUseCase(_build_lmp_gateway())


def build_engineering_list_lmps_dashboard_use_case() -> ListLMPDashboardUseCase:
    return ListLMPDashboardUseCase(_build_lmp_gateway())


def build_engineering_get_lmp_use_case() -> GetLMPUseCase:
    return GetLMPUseCase(_build_lmp_gateway())


def build_engineering_list_transforma_mais_processes_use_case() -> ListProcessUseCase:
    return ListProcessUseCase(_build_transforma_mais_gateway())


def build_engineering_get_transforma_mais_summary_use_case() -> GetProcessSummaryUseCase:
    return GetProcessSummaryUseCase(_build_transforma_mais_gateway())


def build_engineering_metrics_snapshot_service() -> EngineeringMetricsSnapshotService:
    return EngineeringMetricsSnapshotService(
        lmp_dashboard_summary_use_case=build_engineering_get_lmp_dashboard_summary_use_case(),
        transforma_mais_summary_use_case=build_engineering_get_transforma_mais_summary_use_case(),
    )


def build_engineering_indicators_snapshot_provider():
    from si_app.infrastructure.providers.strategic_indicators.engineering_indicators_snapshot_provider import (
        EngineeringIndicatorsSnapshotProvider,
    )

    return EngineeringIndicatorsSnapshotProvider(
        engineering_metrics_snapshot_service=build_engineering_metrics_snapshot_service(),
    )


def build_engineering_get_lmp_dashboard_summary_use_case() -> GetLMPDashboardSummaryUseCase:
    return GetLMPDashboardSummaryUseCase(_build_lmp_gateway())