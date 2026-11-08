"""Port — persistência imutável de lotes MyWEG Necessidades."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol


class MyWegNeedsRepositoryPort(Protocol):
    def find_by_collection_id(self, collection_id: str) -> dict[str, Any] | None:
        ...

    def find_by_id(self, batch_id: str) -> dict[str, Any] | None:
        ...

    def insert_accepted_batch(
        self,
        *,
        collection_id: str,
        branch: str,
        myweg_company_code: str,
        myweg_work_center: str,
        contract_version: str,
        collected_at: datetime,
        exported_at: datetime,
        collection_date: date,
        payload_sha256: str,
        source_files: dict[str, Any],
        record_count: int,
        total_quantidade_un: Decimal,
        total_quantidade_mi: Decimal,
        idempotency_key: str,
        caller_app: str | None,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Insere lote+registros atomicamente. Race em collection_id → UniqueViolation."""
        ...

    def list_batches(
        self,
        *,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def get_latest_batch(self) -> dict[str, Any] | None:
        ...

    def list_batch_records_for_compare(self, *, batch_id: str) -> list[dict[str, Any]]:
        """Linhas do lote + projeção SB1 para comparação/projeção (sem paginação)."""
        ...

    def list_batch_items(
        self,
        *,
        batch_id: str,
        search: str,
        remessa_from: date | None,
        remessa_to: date | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def lookup_delpi_codes_by_materials(
        self, materials: list[str]
    ) -> dict[str, dict[str, str | None]]:
        """Mapa material_weg_tratado → códigos DELPI (verified/informed)."""
        ...

    def lookup_materials_by_delpi_code_search(self, needle: str) -> list[str]:
        """Materiais WEG cujo código DELPI (verificado/informado) contém o termo."""
        ...
