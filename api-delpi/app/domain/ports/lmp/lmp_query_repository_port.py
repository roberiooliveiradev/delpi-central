# app/domain/ports/lmp/lmp_query_repository_port.py
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.lmp.lmp import LMP
from app.application.dto.lmp.list_lmp_request import ListLMPRequest


class LMPQueryRepositoryPort(ABC):

    @abstractmethod
    def list_lmps(
        self,
        request: ListLMPRequest
    ) -> List[LMP]:
        raise NotImplementedError