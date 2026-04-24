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
from app.domain.services.transforma_mais.process_summary_calculator import (
    ProcessSummaryCalculator,
)
from app.infrastructure.persistence.google_sheets.transforma_mais.process_repository import (
    ProcessRepository,
)
from app.infrastructure.persistence.google_sheets.transforma_mais.sheet_sources import (
    TransformaMaisSources,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from app.infrastructure.providers.strategic_indicators.engineering_indicators_snapshot_provider import (
    EngineeringIndicatorsSnapshotProvider,
)
from app.config import settings


def _build_lmp_repository() -> LMPQueryRepository:
    return LMPQueryRepository()


def _build_transforma_mais_sources() -> TransformaMaisSources:
    return TransformaMaisSources(
        sheet_id=settings.TRANSFORMA_MAIS_SHEET_ID,
        tabs={
            "processos": settings.TRANSFORMA_MAIS_GID_PROCESSOS,
            "revisao": settings.TRANSFORMA_MAIS_GID_REVISAO,
            "medicoes": settings.TRANSFORMA_MAIS_GID_MEDICOES,
            "investimentos": settings.TRANSFORMA_MAIS_GID_INVESTIMENTOS,
            "recursos_compartilhados": settings.TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS,
            "revisao_recursos_compartilhados": settings.TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS,
        },
    )


def _build_transforma_mais_repository() -> ProcessRepository:
    client = GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT))
    sources = _build_transforma_mais_sources()

    return ProcessRepository(
        client=client,
        sources=sources,
    )


def _build_transforma_mais_calculator() -> ProcessSummaryCalculator:
    return ProcessSummaryCalculator()


def build_engineering_list_lmps_use_case() -> ListLMPUseCase:
    return ListLMPUseCase(_build_lmp_repository())


def build_engineering_list_lmps_dashboard_use_case() -> ListLMPDashboardUseCase:
    return ListLMPDashboardUseCase(_build_lmp_repository())


def build_engineering_get_lmp_use_case() -> GetLMPUseCase:
    return GetLMPUseCase(_build_lmp_repository())


def build_engineering_list_transforma_mais_processes_use_case() -> ListProcessUseCase:
    return ListProcessUseCase(
        repository=_build_transforma_mais_repository(),
        calculator=_build_transforma_mais_calculator(),
    )


def build_engineering_get_transforma_mais_summary_use_case() -> GetProcessSummaryUseCase:
    return GetProcessSummaryUseCase(
        repository=_build_transforma_mais_repository(),
        calculator=_build_transforma_mais_calculator(),
    )


def build_engineering_metrics_snapshot_service() -> EngineeringMetricsSnapshotService:
    return EngineeringMetricsSnapshotService(
        lmp_dashboard_summary_use_case=build_engineering_get_lmp_dashboard_summary_use_case(),
        transforma_mais_summary_use_case=build_engineering_get_transforma_mais_summary_use_case(),
    )


def build_engineering_indicators_snapshot_provider() -> EngineeringIndicatorsSnapshotProvider:
    return EngineeringIndicatorsSnapshotProvider(
        engineering_metrics_snapshot_service=build_engineering_metrics_snapshot_service(),
    )

def build_engineering_get_lmp_dashboard_summary_use_case() -> GetLMPDashboardSummaryUseCase:
    return GetLMPDashboardSummaryUseCase(_build_lmp_repository())