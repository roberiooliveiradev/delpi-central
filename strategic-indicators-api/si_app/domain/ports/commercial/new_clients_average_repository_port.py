from abc import ABC, abstractmethod

from si_app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from si_app.domain.entities.commercial.new_clients_average import NewClientsAverage


class NewClientsAverageRepositoryPort(ABC):

    @abstractmethod
    def get_new_clients_total(
        self,
        request: NewClientsAverageRequest
    ) -> NewClientsAverage:
        raise NotImplementedError