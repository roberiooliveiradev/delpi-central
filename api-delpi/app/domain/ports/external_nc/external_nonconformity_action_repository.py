# app/domain/ports/external_nc/external_nonconformity_action_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.external_nc.external_nonconformity_action import (
    ExternalNonconformityAction,
)


class ExternalNonconformityActionRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        entity: ExternalNonconformityAction,
    ) -> ExternalNonconformityAction:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        action_id: str,
    ) -> Optional[ExternalNonconformityAction]:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[ExternalNonconformityAction]:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        entity: ExternalNonconformityAction,
    ) -> ExternalNonconformityAction:
        raise NotImplementedError