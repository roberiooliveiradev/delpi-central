# app/composition/lmp_composer.py
from app.application.use_cases.lmp.list_lmp_use_case import ListLMPUseCase
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import LMPQueryRepository
def build_list_lmp_use_case() -> ListLMPUseCase:
    repository = LMPQueryRepository()
    return ListLMPUseCase(repository)