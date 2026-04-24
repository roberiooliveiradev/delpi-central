# app/domain/ports/lmp/lmp_query_repository_port.py
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.lmp.lmp import LMP
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest


class LMPQueryRepositoryPort(ABC):

    @abstractmethod
    def list_lmps(
        self,
        request: ListLMPRequest
    ) -> List[LMP]:
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