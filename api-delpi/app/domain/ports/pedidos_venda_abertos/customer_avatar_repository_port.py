from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.entities.pedidos_venda_abertos.customer_avatar import CustomerAvatarRecord


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
        content_type: str,
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
