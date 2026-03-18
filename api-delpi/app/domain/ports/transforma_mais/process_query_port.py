# app/domain/ports/transforma_mais/process_query_port.py
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.transforma_mais.process import Process
from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse


class ProcessQueryRepositoryPort(ABC):

    @abstractmethod
    def list_process(
        self,
        request: ProcessRequest
    ) -> List[Process]:
        raise NotImplementedError
    
    @abstractmethod
    def get_process_summary(
        self,
        request: ProcessSummaryRequest
    ) -> ProcessSummaryResponse:
        raise NotImplementedError