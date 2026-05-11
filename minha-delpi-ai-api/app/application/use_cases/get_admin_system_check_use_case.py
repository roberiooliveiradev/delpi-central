from app.domain.ports.admin_system_check_repository_port import (
    AdminSystemCheckRepositoryPort,
)


class GetAdminSystemCheckUseCase:
    def __init__(self, system_check_repository: AdminSystemCheckRepositoryPort):
        self.system_check_repository = system_check_repository

    def execute(self) -> dict:
        return self.system_check_repository.check()
