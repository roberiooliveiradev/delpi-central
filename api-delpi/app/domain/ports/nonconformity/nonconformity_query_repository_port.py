# app/domain/ports/nonconformity/nonconformity_query_repository_port.py

from abc import ABC, abstractmethod

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)


class NonconformityQueryRepositoryPort(ABC):

    @abstractmethod
    def list_nonconformities(
        self,
        request: ListNonconformityRequest
    ):
        raise NotImplementedError

    @abstractmethod
    def sum_returned_quantity(
        self,
        request: ListNonconformityRequest,
        *,
        regist_date_start: str | None = None,
        regist_date_end: str | None = None,
    ) -> tuple[float, int]:
        raise NotImplementedError