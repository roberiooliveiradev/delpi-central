from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Sequence
from uuid import UUID

from commercial_app.domain.entities.account_contact import AccountContact
from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.ports.account_contact_repository_port import (
    AccountContactRepositoryPort,
)
from commercial_app.domain.ports.customer_avatar_repository_port import (
    AuditLogRepositoryPort,
)
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.account_audit_formatter_service import (
    AccountAuditFormatterService,
)

AccountScopeCheck = Callable[[str, str], None]

_ENTITY_ACCOUNT = "account"
_ACTION_CONTACT_CREATED = "account.contact.created"
_ACTION_CONTACT_UPDATED = "account.contact.updated"
_ACTION_CONTACT_DELETED = "account.contact.deleted"

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
_FIELD_LABELS_PT = {
    "full_name": "nome",
    "role_title": "cargo",
    "channel": "canal",
    "email": "e-mail",
    "phone_e164": "telefone",
    "is_whatsapp": "WhatsApp",
    "is_primary": "principal",
    "source": "origem",
}


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


def account_entity_id(customer_code: str, customer_store: str) -> str:
    return f"{customer_code}/{customer_store}"


def _row_to_audit_entry(row: dict[str, Any]) -> AuditLogEntry:
    payload = row.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            created_at = None
    return AuditLogEntry(
        id=str(row.get("id") or ""),
        actor_user_id=str(row.get("actor_user_id") or ""),
        action=str(row.get("action") or ""),
        entity_type=str(row.get("entity_type") or ""),
        entity_id=str(row.get("entity_id") or ""),
        payload=payload,
        created_at=created_at if isinstance(created_at, datetime) else None,
    )


def audit_page_to_dict(
    *,
    items: Sequence[dict[str, Any]],
    total: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    return {
        "items": list(items),
        "total": int(total),
        "page": int(page),
        "page_size": int(page_size),
    }


class ManageAccountContactsUseCase:
    def __init__(
        self,
        *,
        repository: AccountContactRepositoryPort,
        audit_repository: AuditLogRepositoryPort | None = None,
        audit_formatter: AccountAuditFormatterService | None = None,
        portfolio_repository: SellerPortfolioRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._audit = audit_repository
        self._audit_formatter = audit_formatter or AccountAuditFormatterService()
        self._portfolios = portfolio_repository

    def _member_user_ids_for_account(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> list[str]:
        if self._portfolios is None:
            return []
        from commercial_app.application.services.commercial_realtime_notify import (
            member_user_ids_for_customer,
        )

        return member_user_ids_for_customer(
            self._portfolios.list_portfolios(active_only=True),
            customer_code=customer_code,
            customer_store=customer_store,
        )

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

    def _append_audit(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        customer_code: str,
        customer_store: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._audit is None:
            return
        actor = (actor_user_id or "").strip()
        if not actor:
            return
        safe_payload = payload or {}
        self._audit.append(
            actor_user_id=actor,
            action=action,
            entity_type=_ENTITY_ACCOUNT,
            entity_id=account_entity_id(customer_code, customer_store),
            payload=safe_payload,
        )
        try:
            from commercial_app.application.services.commercial_realtime_notify import (
                notify_account_changed,
            )
            from commercial_app.core.auth_actor import (
                peek_actor_client_id,
                peek_actor_display_name,
            )

            notify_account_changed(
                reason=action,
                customer_code=customer_code,
                customer_store=customer_store,
                member_user_ids=self._member_user_ids_for_account(
                    customer_code=customer_code,
                    customer_store=customer_store,
                ),
                actor_user_id=actor,
                actor_display_name=peek_actor_display_name(),
                actor_client_id=peek_actor_client_id(),
                payload=safe_payload,
            )
        except Exception:  # noqa: BLE001 — realtime não pode falhar a mutação
            pass

    @staticmethod
    def _contact_audit_payload(
        contact: AccountContact,
        *,
        changed_fields: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contact_id": str(contact.id),
            "full_name": contact.full_name,
            "channel": contact.channel,
            "role_title": contact.role_title,
            "email": contact.email,
            "phone_e164": contact.phone_e164,
            "is_whatsapp": contact.is_whatsapp,
            "is_primary": contact.is_primary,
            "source": contact.source,
        }
        if changed_fields:
            fields = [str(field) for field in changed_fields if field]
            payload["changed_fields"] = fields
            payload["fields_label"] = ", ".join(
                _FIELD_LABELS_PT.get(field, field) for field in fields
            )
        return payload

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
        contact = self._repository.create(values=values)
        self._append_audit(
            actor_user_id=actor,
            action=_ACTION_CONTACT_CREATED,
            customer_code=code,
            customer_store=store,
            payload=self._contact_audit_payload(contact),
        )
        return contact

    def update(
        self,
        *,
        customer_code: str,
        customer_store: str,
        contact_id: UUID,
        changes: dict[str, Any],
        scope_check: AccountScopeCheck,
        actor_user_id: str | None = None,
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
        self._append_audit(
            actor_user_id=actor_user_id,
            action=_ACTION_CONTACT_UPDATED,
            customer_code=code,
            customer_store=store,
            payload=self._contact_audit_payload(
                updated,
                changed_fields=tuple(values.keys()),
            ),
        )
        return updated

    def soft_delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
        contact_id: UUID,
        scope_check: AccountScopeCheck,
        actor_user_id: str | None = None,
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
        self._append_audit(
            actor_user_id=actor_user_id,
            action=_ACTION_CONTACT_DELETED,
            customer_code=code,
            customer_store=store,
            payload=self._contact_audit_payload(deleted),
        )
        return deleted

    def list_account_audit(
        self,
        *,
        customer_code: str,
        customer_store: str,
        scope_check: AccountScopeCheck,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Lista eventos de audit_log da Conta (entity_type=account)."""
        code, store = self._account(customer_code, customer_store)
        self._check_scope(scope_check, customer_code=code, customer_store=store)
        if self._audit is None:
            return audit_page_to_dict(items=[], total=0, page=page, page_size=page_size)

        safe_page = max(1, int(page or 1))
        safe_size = min(100, max(1, int(page_size or 20)))
        rows, total = self._audit.list_for_entity(
            entity_type=_ENTITY_ACCOUNT,
            entity_id=account_entity_id(code, store),
            page=safe_page,
            page_size=safe_size,
        )
        items = [
            self._audit_formatter.format_entry(_row_to_audit_entry(row)) for row in rows
        ]
        return audit_page_to_dict(
            items=items,
            total=total,
            page=safe_page,
            page_size=safe_size,
        )
