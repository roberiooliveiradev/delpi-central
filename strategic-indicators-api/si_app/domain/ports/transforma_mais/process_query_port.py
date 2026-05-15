# app/domain/ports/transforma_mais/process_query_port.py
from abc import ABC, abstractmethod

from si_app.application.dto.transforma_mais.raw_data import TransformaMaisRawData


class ProcessQueryRepositoryPort(ABC):
    @abstractmethod
    def load_raw_data(self) -> TransformaMaisRawData:
        raise NotImplementedError