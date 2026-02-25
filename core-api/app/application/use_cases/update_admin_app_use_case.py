# app/application/use_cases/update_admin_app_use_case.py

from app.application.unit_of_work import UnitOfWork


class UpdateAdminAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str, name: str, description: str | None, icon: str | None):
        self.uow.admin_apps.update_metadata(app_id, name, description, icon)
        self.uow.commit()
        return {"ok": True}