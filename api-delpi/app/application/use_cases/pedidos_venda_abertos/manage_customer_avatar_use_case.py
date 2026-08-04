from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.application.services.pedidos_venda_abertos.customer_avatar_storage import (
    CustomerAvatarStorage,
    CustomerAvatarStorageError,
)
from app.domain.entities.pedidos_venda_abertos.customer_avatar import CustomerAvatarRecord
from app.domain.ports.pedidos_venda_abertos.customer_avatar_repository_port import (
    CustomerAvatarRepositoryPort,
)


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
    ):
        self._repository = repository
        self._storage = storage or CustomerAvatarStorage()

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
            stored_name = self._storage.save(
                customer_code=code,
                customer_store=store,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except CustomerAvatarStorageError as exc:
            raise ValueError(str(exc)) from exc
        return self._repository.upsert(
            customer_code=code,
            customer_store=store,
            file_name=stored_name,
            content_type=(mime_type or "application/octet-stream").lower(),
            uploaded_by_user_id=uploaded_by_user_id,
        )

    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> None:
        code, store = self._normalize_identity(customer_code, customer_store)
        record = self._repository.get(customer_code=code, customer_store=store)
        deleted = self._repository.delete(customer_code=code, customer_store=store)
        if not deleted and record is None:
            raise LookupError("Avatar não encontrado.")
        self._storage.delete(
            customer_code=code,
            customer_store=store,
            file_name=record.file_name if record else None,
        )

    def list_keys_with_avatar(
        self,
        *,
        customers: list[tuple[str, str]],
    ) -> set[tuple[str, str]]:
        records = self._repository.list_for_customers(customers=customers)
        return {(item.customer_code, item.customer_store) for item in records}

    @staticmethod
    def _normalize_identity(customer_code: str, customer_store: str) -> tuple[str, str]:
        code = (customer_code or "").strip()
        store = (customer_store or "").strip()
        if not code or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        return code, store
