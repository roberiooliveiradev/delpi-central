# app/application/use_cases/set_app_active_use_case.py

from app.application.unit_of_work import UnitOfWork


class SetAppActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str, active: bool):
        self.uow.admin_apps.set_active(app_id, active)
        self.uow.commit()
        return {"ok": True}