# app/domain/ports/external_nc/external_nonconformity_root_cause_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.external_nc.external_nonconformity_root_cause import (
    ExternalNonconformityRootCause,
)


class ExternalNonconformityRootCauseRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: ExternalNonconformityRootCause,
    ) -> ExternalNonconformityRootCause:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[ExternalNonconformityRootCause]:
        raise NotImplementedError