# app/composition/nonconformity_composer.py

from app.application.use_cases.nonconformity.list_nonconformity_use_case import (
    ListNonconformityUseCase,
)
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_query_repository import (
    NonconformityQueryRepository,
)


def build_list_nonconformity_use_case() -> ListNonconformityUseCase:
    repository = NonconformityQueryRepository()
    return ListNonconformityUseCase(repository)