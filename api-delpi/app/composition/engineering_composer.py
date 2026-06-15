from __future__ import annotations

from app.application.use_cases.lmp.get_lmp_history_events_use_case import (
    GetLmpHistoryEventsUseCase,
)
from app.application.use_cases.lmp.get_lmp_history_flow_use_case import (
    GetLmpHistoryFlowUseCase,
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
from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_repository import (
    MiniApplicatorsRepository,
)
from app.application.use_cases.mini_applicators.mini_applicators_use_cases import (
    GetMiniApplicatorsFerramentaUseCase,
    GetMiniApplicatorsGolpesUseCase,
    ListMiniApplicatorsComponentesUseCase,
    ListMiniApplicatorsFerramentasUseCase,
    ListMiniApplicatorsPecasUseCase,
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


def build_engineering_get_lmp_history_events_use_case() -> GetLmpHistoryEventsUseCase:
    return GetLmpHistoryEventsUseCase(_build_lmp_repository())


def build_engineering_get_lmp_history_flow_use_case() -> GetLmpHistoryFlowUseCase:
    return GetLmpHistoryFlowUseCase(_build_lmp_repository())


def build_engineering_list_transforma_mais_processes_use_case() -> ListProcessUseCase:
    return ListProcessUseCase(_build_transforma_mais_gateway())


def build_engineering_get_transforma_mais_summary_use_case() -> GetProcessSummaryUseCase:
    return GetProcessSummaryUseCase(_build_transforma_mais_gateway())


def build_engineering_get_lmp_dashboard_summary_use_case() -> GetLMPDashboardSummaryUseCase:
    return GetLMPDashboardSummaryUseCase(_build_lmp_repository())


def _build_mini_applicators_repository() -> MiniApplicatorsRepository:
    return MiniApplicatorsRepository()


def build_list_mini_applicators_ferramentas_use_case() -> ListMiniApplicatorsFerramentasUseCase:
    return ListMiniApplicatorsFerramentasUseCase(_build_mini_applicators_repository())


def build_get_mini_applicators_ferramenta_use_case() -> GetMiniApplicatorsFerramentaUseCase:
    return GetMiniApplicatorsFerramentaUseCase(_build_mini_applicators_repository())


def build_list_mini_applicators_pecas_use_case() -> ListMiniApplicatorsPecasUseCase:
    return ListMiniApplicatorsPecasUseCase(_build_mini_applicators_repository())


def build_get_mini_applicators_golpes_use_case() -> GetMiniApplicatorsGolpesUseCase:
    return GetMiniApplicatorsGolpesUseCase(_build_mini_applicators_repository())


def build_list_mini_applicators_componentes_use_case() -> ListMiniApplicatorsComponentesUseCase:
    return ListMiniApplicatorsComponentesUseCase(_build_mini_applicators_repository())
