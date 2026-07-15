from app.application.use_cases.production_appointments.production_appointments_use_cases import (
    GetProductionAppointmentsSeriesUseCase,
    GetProductionAppointmentsSummaryUseCase,
    ListProductionAppointmentWorkCentersUseCase,
    ListProductionAppointmentsByOpUseCase,
    ListProductionAppointmentsUseCase,
)
from app.infrastructure.persistence.totvs.production_appointments.production_appointments_repository import (
    ProductionAppointmentsRepository,
)


def _repository() -> ProductionAppointmentsRepository:
    return ProductionAppointmentsRepository()


def build_list_production_appointment_work_centers_use_case() -> (
    ListProductionAppointmentWorkCentersUseCase
):
    return ListProductionAppointmentWorkCentersUseCase(repository=_repository())


def build_list_production_appointments_use_case() -> ListProductionAppointmentsUseCase:
    return ListProductionAppointmentsUseCase(repository=_repository())


def build_get_production_appointments_summary_use_case() -> (
    GetProductionAppointmentsSummaryUseCase
):
    return GetProductionAppointmentsSummaryUseCase(repository=_repository())


def build_get_production_appointments_series_use_case() -> (
    GetProductionAppointmentsSeriesUseCase
):
    return GetProductionAppointmentsSeriesUseCase(repository=_repository())


def build_list_production_appointments_by_op_use_case() -> (
    ListProductionAppointmentsByOpUseCase
):
    return ListProductionAppointmentsByOpUseCase(repository=_repository())
