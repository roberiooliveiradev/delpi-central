from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from commercial_app.application.services.customer_avatar_storage import (
    CustomerAvatarStorage,
    CustomerAvatarStorageError,
)
from commercial_app.application.use_cases.manage_account_contacts import account_entity_id
from commercial_app.domain.entities.customer_avatar import CustomerAvatarRecord
from commercial_app.domain.ports.customer_avatar_repository_port import (
    AuditLogRepositoryPort,
    CustomerAvatarRepositoryPort,
)

_ENTITY_ACCOUNT = "account"
_ACTION_AVATAR_UPLOADED = "account.avatar.uploaded"
_ACTION_AVATAR_DELETED = "account.avatar.deleted"


@dataclass(frozen=True, slots=True)
class CustomerAvatarFile:
    path: Path
    content_type: str
    file_name: str


class ManageCustomerAvatarUseCase:
    def __init__(
        self,
        repository: CustomerAvatarRepositoryPort,
        storage: CustomerAvatarStorage | None = None,
        audit_repository: AuditLogRepositoryPort | None = None,
    ):
        self._repository = repository
        self._storage = storage or CustomerAvatarStorage()
        self._audit = audit_repository

    def get_meta(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> CustomerAvatarRecord | None:
        code, store = self._normalize_identity(customer_code, customer_store)
        return self._repository.get(customer_code=code, customer_store=store)

    def get_file(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> CustomerAvatarFile:
        code, store = self._normalize_identity(customer_code, customer_store)
        record = self._repository.get(customer_code=code, customer_store=store)
        if record is None:
            raise LookupError("Avatar não encontrado.")
        try:
            path = self._storage.resolve_file(
                customer_code=code,
                customer_store=store,
                storage_key=record.storage_key,
                file_name=record.file_name,
            )
        except CustomerAvatarStorageError as exc:
            raise LookupError(str(exc)) from exc
        return CustomerAvatarFile(
            path=path,
            content_type=record.content_type,
            file_name=record.file_name,
        )

    def upsert(
        self,
        *,
        customer_code: str,
        customer_store: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        uploaded_by_user_id: str | None,
    ) -> CustomerAvatarRecord:
        code, store = self._normalize_identity(customer_code, customer_store)
        try:
            stored = self._storage.save(
                customer_code=code,
                customer_store=store,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except CustomerAvatarStorageError as exc:
            raise ValueError(str(exc)) from exc
        record = self._repository.upsert(
            customer_code=code,
            customer_store=store,
            file_name=stored.file_name,
            storage_key=stored.storage_key,
            content_type=(mime_type or "application/octet-stream").lower(),
            byte_size=stored.byte_size,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self._append_audit(
            actor_user_id=uploaded_by_user_id,
            action=_ACTION_AVATAR_UPLOADED,
            customer_code=code,
            customer_store=store,
            payload={
                "file_name": record.file_name,
                "content_type": record.content_type,
                "byte_size": record.byte_size,
            },
        )
        return record

    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
        actor_user_id: str | None = None,
    ) -> None:
        code, store = self._normalize_identity(customer_code, customer_store)
        record = self._repository.get(customer_code=code, customer_store=store)
        deleted = self._repository.delete(customer_code=code, customer_store=store)
        if not deleted and record is None:
            raise LookupError("Avatar não encontrado.")
        self._storage.delete(
            customer_code=code,
            customer_store=store,
            storage_key=record.storage_key if record else None,
            file_name=record.file_name if record else None,
        )
        self._append_audit(
            actor_user_id=actor_user_id,
            action=_ACTION_AVATAR_DELETED,
            customer_code=code,
            customer_store=store,
            payload={
                "file_name": record.file_name if record else None,
                "content_type": record.content_type if record else None,
            },
        )

    def list_keys_with_avatar(
        self,
        *,
        customers: list[tuple[str, str]],
    ) -> set[tuple[str, str]]:
        records = self._repository.list_for_customers(customers=customers)
        return {(item.customer_code, item.customer_store) for item in records}

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
        self._audit.append(
            actor_user_id=actor,
            action=action,
            entity_type=_ENTITY_ACCOUNT,
            entity_id=account_entity_id(customer_code, customer_store),
            payload=payload or {},
        )

    @staticmethod
    def _normalize_identity(customer_code: str, customer_store: str) -> tuple[str, str]:
        code = (customer_code or "").strip()
        store = (customer_store or "").strip()
        if not code or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        return code, store
