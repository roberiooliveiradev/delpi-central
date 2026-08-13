from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

from commercial_app.domain.entities.account_contact import AccountContact
from commercial_app.domain.ports.account_contact_repository_port import (
    AccountContactRepositoryPort,
)

AccountScopeCheck = Callable[[str, str], None]
_CHANNELS = frozenset({"phone", "mobile", "email", "whatsapp", "other"})
_UPDATABLE_FIELDS = frozenset(
    {
        "full_name",
        "role_title",
        "channel",
        "email",
        "phone_e164",
        "is_whatsapp",
        "is_primary",
        "source",
    }
)


@dataclass(frozen=True)
class CreateAccountContactInput:
    full_name: str
    channel: str
    role_title: str | None = None
    email: str | None = None
    phone_e164: str | None = None
    is_whatsapp: bool = False
    is_primary: bool = False
    source: str = "manual"


class ManageAccountContactsUseCase:
    def __init__(self, *, repository: AccountContactRepositoryPort) -> None:
        self._repository = repository

    @staticmethod
    def _account(customer_code: str, customer_store: str) -> tuple[str, str]:
        code = (customer_code or "").strip()
        store = (customer_store or "").strip()
        if not code or not store:
            raise ValueError("Informe o código e a loja do cliente.")
        return code, store

    @staticmethod
    def _validate_phone(phone_e164: str | None) -> str | None:
        phone = (phone_e164 or "").strip() or None
        if phone is None:
            return None
        digits = phone[1:] if phone.startswith("+") else ""
        if not digits.isdigit() or not 8 <= len(digits) <= 16:
            raise ValueError(
                "Telefone deve estar no formato E.164: + seguido de 8 a 16 dígitos."
            )
        return phone

    @classmethod
    def _normalize_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(values)
        if "full_name" in normalized:
            normalized["full_name"] = str(normalized["full_name"] or "").strip()
            if not normalized["full_name"]:
                raise ValueError("Nome completo é obrigatório.")
        if "channel" in normalized:
            normalized["channel"] = str(normalized["channel"] or "").strip().lower()
            if normalized["channel"] not in _CHANNELS:
                raise ValueError("Canal de contato inválido.")
        for field in ("role_title", "email"):
            if field in normalized:
                normalized[field] = str(normalized[field] or "").strip() or None
        if "phone_e164" in normalized:
            normalized["phone_e164"] = cls._validate_phone(normalized["phone_e164"])
        if "source" in normalized:
            normalized["source"] = str(normalized["source"] or "").strip() or "manual"
        for field in ("is_whatsapp", "is_primary"):
            if field in normalized:
                normalized[field] = bool(normalized[field])
        return normalized

    @staticmethod
    def _check_scope(
        scope_check: AccountScopeCheck,
        *,
        customer_code: str,
        customer_store: str,
    ) -> None:
        scope_check(customer_code, customer_store)

    def list(
        self,
        *,
        customer_code: str,
        customer_store: str,
        scope_check: AccountScopeCheck,
    ) -> list[AccountContact]:
        code, store = self._account(customer_code, customer_store)
        self._check_scope(scope_check, customer_code=code, customer_store=store)
        return list(
            self._repository.list_for_account(
                customer_code=code,
                customer_store=store,
            )
        )

    def create(
        self,
        *,
        customer_code: str,
        customer_store: str,
        actor_user_id: str,
        data: CreateAccountContactInput,
        scope_check: AccountScopeCheck,
    ) -> AccountContact:
        code, store = self._account(customer_code, customer_store)
        self._check_scope(scope_check, customer_code=code, customer_store=store)
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError("Usuário não identificado.")
        values = self._normalize_values(
            {
                "customer_code": code,
                "customer_store": store,
                "full_name": data.full_name,
                "role_title": data.role_title,
                "channel": data.channel,
                "email": data.email,
                "phone_e164": data.phone_e164,
                "is_whatsapp": data.is_whatsapp,
                "is_primary": data.is_primary,
                "source": data.source,
                "created_by_user_id": actor,
            }
        )
        return self._repository.create(values=values)

    def update(
        self,
        *,
        customer_code: str,
        customer_store: str,
        contact_id: UUID,
        changes: dict[str, Any],
        scope_check: AccountScopeCheck,
    ) -> AccountContact:
        code, store = self._account(customer_code, customer_store)
        self._check_scope(scope_check, customer_code=code, customer_store=store)
        existing = self._repository.get_by_id(contact_id)
        if (
            existing is None
            or existing.customer_code != code
            or existing.customer_store != store
        ):
            raise LookupError("Contato não encontrado.")
        values = self._normalize_values(
            {key: value for key, value in changes.items() if key in _UPDATABLE_FIELDS}
        )
        if not values:
            return existing
        updated = self._repository.update(contact_id=contact_id, values=values)
        if updated is None:
            raise LookupError("Contato não encontrado.")
        return updated

    def soft_delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
        contact_id: UUID,
        scope_check: AccountScopeCheck,
    ) -> AccountContact:
        code, store = self._account(customer_code, customer_store)
        self._check_scope(scope_check, customer_code=code, customer_store=store)
        existing = self._repository.get_by_id(contact_id)
        if (
            existing is None
            or existing.customer_code != code
            or existing.customer_store != store
        ):
            raise LookupError("Contato não encontrado.")
        deleted = self._repository.soft_delete(contact_id=contact_id)
        if deleted is None:
            raise LookupError("Contato não encontrado.")
        return deleted
