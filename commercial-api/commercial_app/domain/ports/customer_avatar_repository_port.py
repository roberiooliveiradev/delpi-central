from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from commercial_app.domain.entities.customer_avatar import CustomerAvatarRecord


class CustomerAvatarRepositoryPort(ABC):
    @abstractmethod
    def get(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> CustomerAvatarRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_customers(
        self,
        *,
        customers: Sequence[tuple[str, str]],
    ) -> list[CustomerAvatarRecord]:
        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        *,
        customer_code: str,
        customer_store: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int | None,
        uploaded_by_user_id: str | None,
    ) -> CustomerAvatarRecord:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> bool:
        raise NotImplementedError


class AuditLogRepositoryPort(ABC):
    @abstractmethod
    def append(
        self,
        *,
        actor_user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_for_entity(
        self,
        *,
        entity_type: str,
        entity_id: str,
        page: int = 1,
        page_size: int = 20,
        related_target_key: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Lista eventos por entidade (mais recentes primeiro) com total.

        When ``related_target_key`` is set (ex.: ``target_portfolio_id``), also
        includes rows whose JSON payload points this entity as transfer target.
        """
        raise NotImplementedError
