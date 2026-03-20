# app/domain/ports/internal_nc/internal_nonconformity_root_cause_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.internal_nc.internal_nonconformity_root_cause import (
    InternalNonconformityRootCause,
)


class InternalNonconformityRootCauseRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: InternalNonconformityRootCause,
    ) -> InternalNonconformityRootCause:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[InternalNonconformityRootCause]:
        raise NotImplementedError

    @abstractmethod
    def exists_for_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> bool:
        raise NotImplementedError