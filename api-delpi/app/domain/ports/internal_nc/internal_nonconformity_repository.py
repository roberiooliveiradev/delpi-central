# app/domain/ports/internal_nc/internal_nonconformity_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)


class InternalNonconformityRepositoryPort(ABC):
    @abstractmethod
    def create(self, entity: InternalNonconformity) -> InternalNonconformity:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, nonconformity_id: str) -> Optional[InternalNonconformity]:
        raise NotImplementedError

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[InternalNonconformity]:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        current_status: Optional[str] = None,
        sector: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, entity: InternalNonconformity) -> InternalNonconformity:
        raise NotImplementedError