# app/domain/ports/internal_nc/internal_nonconformity_effectiveness_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.internal_nc.internal_nonconformity_effectiveness_check import (
    InternalNonconformityEffectivenessCheck,
)


class InternalNonconformityEffectivenessRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: InternalNonconformityEffectivenessCheck,
    ) -> InternalNonconformityEffectivenessCheck:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[InternalNonconformityEffectivenessCheck]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_approved_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> Optional[InternalNonconformityEffectivenessCheck]:
        raise NotImplementedError