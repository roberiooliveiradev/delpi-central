# app/application/use_cases/nonconformity/list_nonconformity_use_case.py

from si_app.application.models.page import Page
from si_app.domain.entities.nonconformity.nonconformity import Nonconformity
from si_app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from si_app.domain.ports.nonconformity.nonconformity_query_repository_port import (
    NonconformityQueryRepositoryPort,
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

        if request.type not in {"internal", "external", "all"}:
            raise ValueError("type deve ser internal, external ou all")

        return self._repository.list_nonconformities(request)