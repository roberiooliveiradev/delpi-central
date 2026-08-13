from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.account_contact import AccountContact


class AccountContactRepositoryPort(ABC):
    @abstractmethod
    def list_for_account(
        self, *, customer_code: str, customer_store: str
    ) -> Sequence[AccountContact]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, contact_id: UUID) -> AccountContact | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, *, values: dict[str, Any]) -> AccountContact:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, *, contact_id: UUID, values: dict[str, Any]
    ) -> AccountContact | None:
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, *, contact_id: UUID) -> AccountContact | None:
        raise NotImplementedError
