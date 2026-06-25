from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)


class OverallEquipmentEffectivenessRepositoryPort(ABC):
    @abstractmethod
    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest,
    ) -> OverallEquipmentEffectiveness:
        raise NotImplementedError

    @abstractmethod
    def list_overall_equipment_effectiveness_by_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_oee_appointments_bundle(
        self,
        request: GetProductionOeeRequest,
    ) -> tuple[dict, Page[dict]]:
        raise NotImplementedError

    @abstractmethod
    def get_oee_appointment_summary(
        self,
        request: GetProductionOeeRequest,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_oee_appointments(
        self,
        request: GetProductionOeeRequest,
    ) -> Page[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_oee_appointment_by_id(
        self,
        appointment_id: int,
        *,
        branch: str | None = None,
    ) -> dict | None:
        raise NotImplementedError