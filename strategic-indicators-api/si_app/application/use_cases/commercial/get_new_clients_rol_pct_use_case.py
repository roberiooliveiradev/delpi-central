from si_app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from si_app.domain.ports.commercial.new_clients_rol_pct_repository_port import NewClientsRolPctRepositoryPort


class GetNewClientsRolPctUseCase:
    def __init__(
        self,
        new_clients_rol_pct_repository: NewClientsRolPctRepositoryPort
    ):
        self._new_clients_rol_pct_repository = new_clients_rol_pct_repository

    def execute(self, request: NewClientsRolPctRequest) -> dict:
        indicator = self._new_clients_rol_pct_repository.get_new_clients_rol_pct(request)

        return {
            "branch": indicator.branch,
            "start_date": indicator.start_date,
            "end_date": indicator.end_date,
            "total_rol": indicator.total_rol,
            "new_clients_rol": indicator.new_clients_rol,
            "new_clients_rol_pct": indicator.new_clients_rol_pct,
        }