# app/application/use_cases/delete_admin_app_use_case.py

from app.application.unit_of_work import UnitOfWork


class DeleteAdminAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str):
        self.uow.admin_apps.delete(app_id)
        self.uow.commit()
        return {"ok": True}