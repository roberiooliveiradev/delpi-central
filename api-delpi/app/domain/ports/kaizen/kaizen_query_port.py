# app/domain/ports/kaizen/kaizen_query_port.py
from abc import ABC, abstractmethod
from typing import List

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse


class KaizenQueryRepositoryPort(ABC):
    
    @abstractmethod
    def get_kaizen_summary(
        self, 
        request: KaizenSummaryRequest
    )->KaizenSummaryResponse:
        raise NotImplementedError