from abc import ABC, abstractmethod
from datetime import date
from typing import List

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.models.page import Page
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent
from app.domain.entities.lmp.lmp_product import LMPProduct


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
    def list_ov_products(
        self,
        *,
        sale_number: str,
        requested_branch: str | None = None,
    ) -> list[LMPProduct]:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_panel_context(self, request: GetLMPRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_lmp_history_panel_context(self, request: GetLmpHistoryRequest) -> dict:
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

    def get_lmp_dashboard_summary_facts(self, request: ListLMPRequest) -> list[dict]:
        """Fatos do summary sem BOM/PI. Default: delega ao summary sem PI."""
        return self.get_lmp_dashboard_summary(request)

    def get_lmp_pi_counts_by_ovs(
        self,
        *,
        ov_keys: list[dict],
        requested_branch: str | None = None,
    ) -> dict[tuple[str, str, str], int]:
        """Contagem de PI scoped por OV. Default vazio para stubs de teste."""
        del ov_keys, requested_branch
        return {}

    def get_earliest_ov_date(self) -> date | None:
        """Opcional: data da primeira OV (AD1). Default None para stubs de teste."""
        return None