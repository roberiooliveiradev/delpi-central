from abc import ABC, abstractmethod


class PpmQueryRepositoryPort(ABC):

    @abstractmethod
    def get_nc_returned_total(self, request) -> float:
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
