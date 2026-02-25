# app/application/use_cases/create_role_use_case.py

class CreateRoleUseCase:

    def __init__(self, uow):
        self.uow = uow

    def execute(self, name: str, description: str | None):

        if self.uow.roles.exists_by_name(name):
            raise ValueError("Role já existe")

        role_id = self.uow.roles.create(name, description)

        self.uow.commit()

        return role_id