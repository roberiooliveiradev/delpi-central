# app/domain/ports/internal_nc/internal_nonconformity_action_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.internal_nc.internal_nonconformity_action import (
    InternalNonconformityAction,
)


class InternalNonconformityActionRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: InternalNonconformityAction,
    ) -> InternalNonconformityAction:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        action_id: str,
    ) -> Optional[InternalNonconformityAction]:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[InternalNonconformityAction]:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        entity: InternalNonconformityAction,
    ) -> InternalNonconformityAction:
        raise NotImplementedError