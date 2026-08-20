"""Composition — carga máquina."""

from __future__ import annotations

from app.application.use_cases.production.get_production_machine_load_use_cases import (
    GetProductionMachineLoadAppointmentStatusUseCase,
    GetProductionMachineLoadOperationsUseCase,
    GetProductionMachineLoadWorkCentersUseCase,
)
from app.infrastructure.persistence.totvs.production.machine_load_repository import (
    MachineLoadRepository,
)


def build_get_production_machine_load_work_centers_use_case() -> (
    GetProductionMachineLoadWorkCentersUseCase
):
    return GetProductionMachineLoadWorkCentersUseCase(
        repository=MachineLoadRepository()
    )


def build_get_production_machine_load_operations_use_case() -> (
    GetProductionMachineLoadOperationsUseCase
):
    return GetProductionMachineLoadOperationsUseCase(repository=MachineLoadRepository())


def build_get_production_machine_load_appointment_status_use_case() -> (
    GetProductionMachineLoadAppointmentStatusUseCase
):
    return GetProductionMachineLoadAppointmentStatusUseCase(
        repository=MachineLoadRepository()
    )
