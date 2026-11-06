"""Port — persistência imutável de observações MyWEG NF Emitidas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol


class MyWegInvoiceObservationsRepositoryPort(Protocol):
    def find_by_collection_id(self, collection_id: str) -> dict[str, Any] | None:
        ...

    def find_by_id(self, observation_id: str) -> dict[str, Any] | None:
        ...

    def insert_accepted_observation(
        self,
        *,
        collection_id: str,
        branch: str,
        myweg_company_code: str,
        myweg_work_center: str,
        myweg_supplier_code: str,
        contract_version: str,
        document_date: date,
        observation_status: str,
        observed_at: datetime | None,
        source_prepared_at: datetime,
        source_sha256: str | None,
        payload_sha256: str,
        semantic_sha256: str,
        record_count: int,
        total_quantity_un: Decimal,
        manifesto: dict[str, Any],
        idempotency_key: str,
        caller_app: str | None,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Insere observação+itens atomicamente. Race em collection_id → UniqueViolation."""
        ...

    def list_observations(
        self,
        *,
        document_date: date | None,
        observation_status: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def list_observation_items(
        self,
        *,
        observation_id: str,
        search: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def count_by_semantic_sha256(
        self, *, semantic_sha256: str, exclude_collection_id: str | None = None
    ) -> int:
        ...
