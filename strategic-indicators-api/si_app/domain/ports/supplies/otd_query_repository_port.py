from abc import ABC, abstractmethod
from si_app.application.dto.supplies.get_otd_request import GetOTDRequest


class OtdQueryRepositoryPort(ABC):

    @abstractmethod
    def get_otd_summary(self, request: GetOTDRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_otd_monthly_breakdown(self, request: GetOTDRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_top_late_suppliers(self, request: GetOTDRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_late_deliveries(self, request: GetOTDRequest) -> list[dict]:
        raise NotImplementedError