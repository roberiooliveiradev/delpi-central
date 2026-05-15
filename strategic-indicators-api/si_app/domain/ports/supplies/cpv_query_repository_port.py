from abc import ABC, abstractmethod
from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest


class CpvQueryRepositoryPort(ABC):

    @abstractmethod
    def get_cpv_summary(self, request: GetCPVRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_cpv_by_cfop(self, request: GetCPVRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_cpv_by_tm(self, request: GetCPVRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_cpv_top_products(self, request: GetCPVRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_cpv_top_documents(self, request: GetCPVRequest) -> list[dict]:
        raise NotImplementedError