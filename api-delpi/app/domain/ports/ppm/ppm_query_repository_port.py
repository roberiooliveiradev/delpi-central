# app/domain/ports/ppm/ppm_query_repository_port.py

from abc import ABC, abstractmethod


class PpmQueryRepositoryPort(ABC):

    @abstractmethod
    def get_summary(self, request):
        raise NotImplementedError

    @abstractmethod
    def list_produced_quantity(self, request):
        raise NotImplementedError

    @abstractmethod
    def list_items(self, request):
        raise NotImplementedError

    @abstractmethod
    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        raise NotImplementedError