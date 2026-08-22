from functools import lru_cache

from travel_expenses_app.application.use_cases.travel_report_service import TravelReportService
from travel_expenses_app.infrastructure.persistence.repositories.postgres_report_repository import (
    PostgresTravelReportRepository,
)


@lru_cache(maxsize=1)
def get_travel_report_service() -> TravelReportService:
    return TravelReportService(PostgresTravelReportRepository())
