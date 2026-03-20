# app/domain/ports/external_nc/external_nonconformity_effectiveness_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.external_nc.external_nonconformity_effectiveness_check import (
    ExternalNonconformityEffectivenessCheck,
)


class ExternalNonconformityEffectivenessRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: ExternalNonconformityEffectivenessCheck,
    ) -> ExternalNonconformityEffectivenessCheck:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[ExternalNonconformityEffectivenessCheck]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_approved_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> Optional[ExternalNonconformityEffectivenessCheck]:
        raise NotImplementedError