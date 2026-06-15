# app/domain/ports/kaizen/kaizen_query_port.py
from abc import ABC, abstractmethod
from typing import Optional

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from app.domain.entities.kaizen.kaizen import KaizenDetail


class KaizenQueryRepositoryPort(ABC):

    @abstractmethod
    def get_kaizen_summary(
        self,
        request: KaizenSummaryRequest,
    ) -> KaizenSummaryResponse:
        raise NotImplementedError

    @abstractmethod
    def get_kaizen_by_id(self, kaizen_id: str) -> Optional[KaizenDetail]:
        raise NotImplementedError

    @abstractmethod
    def list_active_kaizen_details(self) -> list[KaizenDetail]:
        raise NotImplementedError