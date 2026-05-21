from __future__ import annotations

from app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)
from app.application.use_cases.lmp.get_lmp_use_case import GetLMPUseCase
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    ListLMPDashboardUseCase,
)
from app.application.use_cases.lmp.list_lmp_use_case import ListLMPUseCase
from app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)
from app.application.use_cases.transforma_mais.list_process_use_case import (
    ListProcessUseCase,
)
from app.application.use_cases.lmp.get_lmp_dashboard_summary_use_case import (
    GetLMPDashboardSummaryUseCase,
)
from app.infrastructure.gateways.transformometro_transforma_mais_gateway import (
    TransformometroTransformaMaisGateway,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)


def _build_lmp_repository() -> LMPQueryRepository:
    return LMPQueryRepository()


def _build_transforma_mais_gateway() -> TransformometroTransformaMaisGateway:
    return TransformometroTransformaMaisGateway()


def build_engineering_list_lmps_use_case() -> ListLMPUseCase:
    return ListLMPUseCase(_build_lmp_repository())


def build_engineering_list_lmps_dashboard_use_case() -> ListLMPDashboardUseCase:
    return ListLMPDashboardUseCase(_build_lmp_repository())


def build_engineering_get_lmp_use_case() -> GetLMPUseCase:
    return GetLMPUseCase(_build_lmp_repository())


def build_engineering_list_transforma_mais_processes_use_case() -> ListProcessUseCase:
    return ListProcessUseCase(_build_transforma_mais_gateway())


def build_engineering_get_transforma_mais_summary_use_case() -> GetProcessSummaryUseCase:
    return GetProcessSummaryUseCase(_build_transforma_mais_gateway())


def build_engineering_metrics_snapshot_service() -> EngineeringMetricsSnapshotService:
    return EngineeringMetricsSnapshotService(
        lmp_dashboard_summary_use_case=build_engineering_get_lmp_dashboard_summary_use_case(),
        transforma_mais_summary_use_case=build_engineering_get_transforma_mais_summary_use_case(),
    )


def build_engineering_get_lmp_dashboard_summary_use_case() -> GetLMPDashboardSummaryUseCase:
    return GetLMPDashboardSummaryUseCase(_build_lmp_repository())
