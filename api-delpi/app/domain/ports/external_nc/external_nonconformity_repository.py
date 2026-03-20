# app/domain/ports/external_nc/external_nonconformity_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.external_nc.external_nonconformity import (
    ExternalNonconformity,
)


class ExternalNonconformityRepositoryPort(ABC):
    @abstractmethod
    def create(self, entity: ExternalNonconformity) -> ExternalNonconformity:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, nonconformity_id: str) -> Optional[ExternalNonconformity]:
        raise NotImplementedError

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[ExternalNonconformity]:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        current_status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, entity: ExternalNonconformity) -> ExternalNonconformity:
        raise NotImplementedError