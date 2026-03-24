# app/composition/ppm_composer.py

from app.application.use_cases.ppm.get_ppm_summary_use_case import GetPpmSummaryUseCase
from app.application.use_cases.ppm.list_ppm_use_case import ListPpmUseCase
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)


def build_get_ppm_summary_use_case() -> GetPpmSummaryUseCase:
    repository = PpmQueryRepository()
    return GetPpmSummaryUseCase(repository)


def build_list_ppm_use_case() -> ListPpmUseCase:
    repository = PpmQueryRepository()
    return ListPpmUseCase(repository)