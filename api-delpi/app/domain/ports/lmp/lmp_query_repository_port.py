from abc import ABC, abstractmethod
from typing import List

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.models.page import Page
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent


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
    def get_lmp_panel_context(self, request: GetLMPRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_history_events(
        self,
        request: GetLmpHistoryRequest,
    ) -> list[LMPHistoryEvent]:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_history_flow(
        self,
        request: GetLmpHistoryRequest,
    ) -> list[LMPHistoryEvent]:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_dashboard_summary(self, request: ListLMPRequest) -> list[dict]:
        raise NotImplementedError