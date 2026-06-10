# app/application/use_cases/reset_portal_tour_progress_use_case.py

from app.application.unit_of_work import UnitOfWork


class ResetPortalTourProgressUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> None:
        self.uow.portal_tour.delete_progress(user_id)
