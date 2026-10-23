"""Use case — itens de catálogo SA2 para o cadastro de fornecedores.

Valida a allowlist de catálogos e a dependência de UF (``municipalities``)
antes de delegar ao repositório TOTVS read-only.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_catalogs_repository import (
    SUPPLIER_CATALOG_KINDS,
    catalog_requires_state,
    catalog_supports_code_filter,
)


class SupplierCatalogRepositoryPort(Protocol):
    def list_catalog_items(
        self,
        catalog: str,
        *,
        query: str | None,
        state: str | None,
        code: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], bool]: ...


class ListSupplierCatalogItemsUseCase:
    def __init__(self, repository: SupplierCatalogRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        catalog: str,
        *,
        query: str | None = None,
        state: str | None = None,
        code: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        kind = (catalog or "").strip().lower()
        if kind not in SUPPLIER_CATALOG_KINDS:
            raise ValueError(
                "Catálogo desconhecido. Permitidos: "
                + ", ".join(SUPPLIER_CATALOG_KINDS)
            )
        if catalog_requires_state(kind) and not (state or "").strip():
            raise ValueError(
                "O catálogo 'municipalities' exige o parâmetro 'state' (UF)."
            )
        code_arg = (code or "").strip() or None
        if code_arg and not catalog_supports_code_filter(kind):
            raise ValueError(
                f"O catálogo '{kind}' não aceita o parâmetro 'code'."
            )

        items, has_more = self._repository.list_catalog_items(
            kind,
            query=(query or "").strip() or None,
            state=(state or "").strip().upper() or None,
            code=code_arg,
            limit=limit,
        )
        return {
            "catalog": kind,
            "items": items,
            "has_more": has_more,
            "total": len(items),
        }
