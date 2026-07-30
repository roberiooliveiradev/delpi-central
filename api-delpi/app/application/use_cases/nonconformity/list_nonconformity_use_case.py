# app/application/use_cases/nonconformity/list_nonconformity_use_case.py

from app.application.models.page import Page
from app.domain.entities.nonconformity.nonconformity import Nonconformity
from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.domain.ports.nonconformity.nonconformity_query_repository_port import (
    NonconformityQueryRepositoryPort,
)
from app.domain.services.quality.nonconformity_query_filter_service import (
    normalize_nonconformity_filter_type,
)


class ListNonconformityUseCase:

    def __init__(
        self,
        repository: NonconformityQueryRepositoryPort
    ):
        self._repository = repository

    def execute(
        self,
        request: ListNonconformityRequest
    ) -> Page[Nonconformity]:

        request.type = normalize_nonconformity_filter_type(request.type)

        return self._repository.list_nonconformities(request)