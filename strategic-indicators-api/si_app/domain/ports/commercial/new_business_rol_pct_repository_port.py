from abc import ABC, abstractmethod

from si_app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from si_app.domain.entities.commercial.new_business_rol_pct import NewBusinessRolPct


class NewBusinessRolPctRepositoryPort(ABC):
    @abstractmethod
    def get_new_business_rol_pct(self, request: NewBusinessRolPctRequest) -> NewBusinessRolPct:
        raise NotImplementedError
