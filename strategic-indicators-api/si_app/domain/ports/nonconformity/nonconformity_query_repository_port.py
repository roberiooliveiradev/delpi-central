# app/domain/ports/nonconformity/nonconformity_query_repository_port.py

from abc import ABC, abstractmethod

from si_app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)


class NonconformityQueryRepositoryPort(ABC):

    @abstractmethod
    def list_nonconformities(
        self,
        request: ListNonconformityRequest
    ):
        raise NotImplementedError