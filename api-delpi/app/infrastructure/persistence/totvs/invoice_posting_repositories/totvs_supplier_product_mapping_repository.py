"""Leitura em lote da relação Produto x Fornecedor. Não grava no Protheus."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.invoice_posting_repositories.supplier_product_mapping_sql import (
    CHUNK_SIZE,
    chunk_supplier_product_codes,
    supplier_product_mapping_sql,
)


class TotvsSupplierProductMappingRepository(BaseRepository):
    def list_mappings(
        self,
        *,
        supplier_code: str,
        supplier_store: str,
        supplier_product_codes: list[str],
        chunk_size: int = CHUNK_SIZE,
    ) -> list[dict[str, str]]:
        codes = [code for code in supplier_product_codes if code]
        if not codes:
            return []
        found: list[dict[str, str]] = []
        for chunk in chunk_supplier_product_codes(codes, chunk_size):
            sql = supplier_product_mapping_sql(len(chunk))
            params = (supplier_code, supplier_store, *chunk)
            found.extend(self._fetch_preserving_codes(sql, params))
        return found

    def _fetch_preserving_codes(self, sql: str, params: tuple) -> list[dict[str, str]]:
        """RTRIM já tirou o padding CHAR. Não aplicar strip, para não apagar espaço inicial."""

        with self as repo:
            repo.cursor.execute(sql, params)
            rows = repo.cursor.fetchall()
            columns = [desc[0] for desc in repo.cursor.description]
        mapped: list[dict[str, str]] = []
        for row in rows:
            item: dict[str, str] = {}
            for key, value in zip(columns, row):
                item[str(key)] = "" if value is None else str(value)
            mapped.append(item)
        return mapped
