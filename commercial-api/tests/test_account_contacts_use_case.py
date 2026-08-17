from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest

from commercial_app.application.use_cases.manage_account_contacts import (
    CreateAccountContactInput,
    ManageAccountContactsUseCase,
)
from commercial_app.domain.entities.account_contact import AccountContact


class InMemoryAccountContactRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, AccountContact] = {}

    def list_for_account(
        self, *, customer_code: str, customer_store: str
    ) -> list[AccountContact]:
        return sorted(
            [
                item
                for item in self.items.values()
                if item.customer_code == customer_code
                and item.customer_store == customer_store
                and item.deleted_at is None
            ],
            key=lambda item: (not item.is_primary, item.full_name),
        )

    def get_by_id(self, contact_id: UUID) -> AccountContact | None:
        item = self.items.get(contact_id)
        return item if item and item.deleted_at is None else None

    def _clear_primary(self, customer_code: str, customer_store: str) -> None:
        now = datetime.now(timezone.utc)
        for contact_id, item in list(self.items.items()):
            if (
                item.customer_code == customer_code
                and item.customer_store == customer_store
                and item.deleted_at is None
                and item.is_primary
            ):
                self.items[contact_id] = replace(
                    item,
                    is_primary=False,
                    updated_at=now,
                )

    def create(self, *, values: dict[str, Any]) -> AccountContact:
        if values["is_primary"]:
            self._clear_primary(values["customer_code"], values["customer_store"])
        now = datetime.now(timezone.utc)
        contact = AccountContact(
            id=uuid4(),
            customer_code=values["customer_code"],
            customer_store=values["customer_store"],
            full_name=values["full_name"],
            role_title=values.get("role_title"),
            channel=values["channel"],
            email=values.get("email"),
            phone_e164=values.get("phone_e164"),
            is_whatsapp=values["is_whatsapp"],
            is_primary=values["is_primary"],
            source=values["source"],
            deleted_at=None,
            created_at=now,
            updated_at=now,
            created_by_user_id=values["created_by_user_id"],
        )
        self.items[contact.id] = contact
        return contact

    def update(
        self, *, contact_id: UUID, values: dict[str, Any]
    ) -> AccountContact | None:
        current = self.get_by_id(contact_id)
        if current is None:
            return None
        if values.get("is_primary") is True:
            self._clear_primary(current.customer_code, current.customer_store)
            current = self.items[contact_id]
        updated = replace(
            current,
            **values,
            updated_at=datetime.now(timezone.utc),
        )
        self.items[contact_id] = updated
        return updated

    def soft_delete(self, *, contact_id: UUID) -> AccountContact | None:
        current = self.get_by_id(contact_id)
        if current is None:
            return None
        deleted = replace(
            current,
            is_primary=False,
            deleted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.items[contact_id] = deleted
        return deleted


def allow_scope(_customer_code: str, _customer_store: str) -> None:
    return None


def test_create_list_primary_update_and_soft_delete() -> None:
    repository = InMemoryAccountContactRepository()
    use_case = ManageAccountContactsUseCase(repository=repository)

    first = use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(
            full_name="Ana Souza",
            channel="whatsapp",
            phone_e164="+5511999999999",
            is_whatsapp=True,
            is_primary=True,
        ),
        scope_check=allow_scope,
    )
    second = use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(
            full_name="Bruno Lima",
            channel="email",
            email="bruno@example.com",
            is_primary=True,
        ),
        scope_check=allow_scope,
    )

    items = use_case.list(
        customer_code="000001",
        customer_store="01",
        scope_check=allow_scope,
    )
    assert [item.id for item in items] == [second.id, first.id]
    assert sum(item.is_primary for item in items) == 1
    assert items[0].is_primary is True

    promoted = use_case.update(
        customer_code="000001",
        customer_store="01",
        contact_id=first.id,
        changes={"is_primary": True, "role_title": "Compras"},
        scope_check=allow_scope,
    )
    assert promoted.is_primary is True
    assert promoted.role_title == "Compras"
    assert repository.get_by_id(second.id).is_primary is False  # type: ignore[union-attr]

    use_case.soft_delete(
        customer_code="000001",
        customer_store="01",
        contact_id=first.id,
        scope_check=allow_scope,
    )
    remaining = use_case.list(
        customer_code="000001",
        customer_store="01",
        scope_check=allow_scope,
    )
    assert [item.id for item in remaining] == [second.id]
    assert repository.get_by_id(first.id) is None


@pytest.mark.parametrize(
    "phone",
    [
        "5511999999999",
        "+55 11 99999-9999",
        "+1234567",
        "+12345678901234567",
    ],
)
def test_rejects_invalid_e164_phone(phone: str) -> None:
    use_case = ManageAccountContactsUseCase(
        repository=InMemoryAccountContactRepository()
    )

    with pytest.raises(ValueError, match="E.164"):
        use_case.create(
            customer_code="000001",
            customer_store="01",
            actor_user_id="user-1",
            data=CreateAccountContactInput(
                full_name="Ana Souza",
                channel="mobile",
                phone_e164=phone,
            ),
            scope_check=allow_scope,
        )


def test_customer_scope_is_required_for_edits() -> None:
    use_case = ManageAccountContactsUseCase(
        repository=InMemoryAccountContactRepository()
    )

    def deny_scope(_customer_code: str, _customer_store: str) -> None:
        raise LookupError("Cliente fora do escopo.")

    with pytest.raises(LookupError, match="fora do escopo"):
        use_case.create(
            customer_code="000001",
            customer_store="01",
            actor_user_id="user-1",
            data=CreateAccountContactInput(
                full_name="Ana Souza",
                channel="email",
            ),
            scope_check=deny_scope,
        )
