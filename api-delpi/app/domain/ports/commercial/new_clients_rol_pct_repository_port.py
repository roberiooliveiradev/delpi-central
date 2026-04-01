from abc import ABC, abstractmethod

from app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from app.domain.entities.commercial.new_clients_rol_pct import NewClientsRolPct


class NewClientsRolPctRepositoryPort(ABC):

    @abstractmethod
    def get_new_clients_rol_pct(
        self,
        request: NewClientsRolPctRequest
    ) -> NewClientsRolPct:
        raise NotImplementedError