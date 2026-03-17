# app/composition/lmp_composer.py
from app.application.use_cases.lmp.list_lmp_use_case import ListLMPUseCase
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import ListLMPDashboardUseCase
from app.application.use_cases.lmp.get_lmp_use_case import GetLMPUseCase
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import LMPQueryRepository


def build_list_lmp_use_case() -> ListLMPUseCase:
    repository = LMPQueryRepository()
    return ListLMPUseCase(repository)


def build_list_lmp_dashboard_use_case() -> ListLMPDashboardUseCase:
    repository = LMPQueryRepository()
    return ListLMPDashboardUseCase(repository)


def build_get_lmp_use_case() -> GetLMPUseCase:
    repository = LMPQueryRepository()
    return GetLMPUseCase(repository)