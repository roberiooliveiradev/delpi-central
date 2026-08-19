from app.application.dto.production_appointments.production_appointments_query_request import (
    ProductionAppointmentsQueryRequest,
)
from app.application.use_cases.production_appointments.production_appointments_use_cases import (
    GetProductionAppointmentsSummaryUseCase,
)


class _FakeSummaryRepository:
    def __init__(self) -> None:
        self.totals_kwargs: dict = {}

    def get_summary_by_ct(self, **kwargs) -> list[dict]:
        return [
            {
                "work_center": "CT-23",
                "work_center_name": "CORTE",
                "is_final_inspection": 0,
                "qty_produced": 100.0,
            }
        ]

    def get_summary_totals(self, **kwargs) -> dict:
        self.totals_kwargs = kwargs
        return {
            "appointment_count": 10,
            "qty_produced": 50.0,
            "qty_lost": 2.0,
            "op_count": 3,
            "work_center_count": 2,
        }


def test_summary_totals_declare_pa_last_routing_scope_without_work_center() -> None:
    repo = _FakeSummaryRepository()
    result = GetProductionAppointmentsSummaryUseCase(repo).execute(
        ProductionAppointmentsQueryRequest.from_query(
            branch="01",
            date_start="2026-08-01",
            date_end="2026-08-18",
        )
    )
    assert result["totals"]["qty_produced"] == 50.0
    assert result["totals"]["qty_produced_scope"] == "pa_last_routing_operation"
    assert result["items"][0]["work_center"] == "CT-23"


def test_summary_totals_declare_work_center_scope_when_filtered() -> None:
    repo = _FakeSummaryRepository()
    result = GetProductionAppointmentsSummaryUseCase(repo).execute(
        ProductionAppointmentsQueryRequest.from_query(
            branch="01",
            date_start="2026-08-01",
            date_end="2026-08-18",
            work_center="CT-23",
        )
    )
    assert result["totals"]["qty_produced_scope"] == "work_center"
    assert repo.totals_kwargs["work_center"] == "CT-23"
