from abc import ABC, abstractmethod
from typing import List

from si_app.application.dto.lmp.get_lmp_request import GetLMPRequest
from si_app.application.dto.lmp.list_lmp_request import ListLMPRequest
from si_app.application.models.page import Page
from si_app.domain.entities.lmp.lmp import LMP


class LMPQueryRepositoryPort(ABC):

    @abstractmethod
    def list_lmps(
        self,
        request: ListLMPRequest
    ) -> List[LMP]:
        raise NotImplementedError

    @abstractmethod
    def list_lmps_page(
        self,
        request: ListLMPRequest
    ) -> Page[LMP]:
        raise NotImplementedError

    @abstractmethod
    def get_lmp(
        self,
        request: GetLMPRequest
    ) -> LMP:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_dashboard_summary(self, request: ListLMPRequest) -> list[dict]:
        raise NotImplementedError