from abc import ABC, abstractmethod

from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.domain.entities.commercial.new_clients_average import NewClientsAverage


class NewClientsAverageRepositoryPort(ABC):

    @abstractmethod
    def get_new_clients_total(
        self,
        request: NewClientsAverageRequest
    ) -> NewClientsAverage:
        raise NotImplementedError