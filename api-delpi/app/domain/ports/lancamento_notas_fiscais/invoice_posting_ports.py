"""Ports — lançamento-notas-fiscais."""
from __future__ import annotations

from typing import Any, Protocol, Sequence


class SupplierQueryPort(Protocol):
    def search_suppliers(
        self,
        *,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]: ...

    def get_supplier(
        self,
        *,
        supplier_code: str,
        supplier_store: str,
    ) -> dict[str, Any] | None: ...


class InvoicePostingSf1QueryPort(Protocol):
    """Consulta somente leitura à SF1010 (cabeçalho NF entrada)."""

    def find_active_by_fiscal_keys(
        self,
        keys: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...


class InvoicePostingReconciliationLockPort(Protocol):
    def try_acquire_reconciliation_lock(self) -> bool: ...

    def release_reconciliation_lock(self) -> None: ...

    def is_reconciliation_refresh_cooldown_active(
        self,
        cooldown_seconds: int,
    ) -> bool: ...

    def mark_reconciliation_refresh_started(self) -> None: ...


class InvoicePostingRequestPort(Protocol):
    def find_active_by_fiscal_key(
        self,
        *,
        branch_code: str,
        supplier_code: str,
        supplier_store: str,
        document_match_key: str,
        series: str,
        exclude_id: str | None = None,
    ) -> dict[str, Any] | None: ...

    def create_request_with_history(
        self,
        *,
        request_fields: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]: ...

    def get_request(self, request_id: str) -> dict[str, Any] | None: ...

    def list_history(self, request_id: str) -> list[dict[str, Any]]: ...

    def list_comments(self, request_id: str) -> list[dict[str, Any]]: ...

    def list_requests(
        self,
        *,
        filters: dict[str, Any],
        created_by_user_id: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]: ...

    def list_reconciliation_candidates(
        self,
        *,
        limit: int,
    ) -> list[dict[str, Any]]: ...

    def mark_reconciled_posted_batch(
        self,
        items: Sequence[dict[str, Any]],
    ) -> int: ...

    def update_request_with_history(
        self,
        *,
        request_id: str,
        updates: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]: ...

    def add_comment(
        self,
        *,
        request_id: str,
        author_user_id: str,
        author_name: str,
        body: str,
    ) -> dict[str, Any]: ...

    def try_acquire_reconciliation_lock(self) -> bool: ...

    def release_reconciliation_lock(self) -> None: ...

    def is_reconciliation_refresh_cooldown_active(
        self,
        cooldown_seconds: int,
    ) -> bool: ...

    def mark_reconciliation_refresh_started(self) -> None: ...
