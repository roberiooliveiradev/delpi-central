"""E-NC-11 — contexto OV/produto/BOM de uma NC via fatos oficiais.

Compõe: registro NC (repositório Engineering) + fato oficial da OV
(F-LMP-02, api-delpi via ``LmpFactsSource``) + estrutura/BOM dos produtos
associados (Products, via fonte auxiliar delegada). Estados honestos por
fonte — ``available``/``not_found``/``forbidden``/``unavailable``, nunca
payload inventado.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.lmp_facts import LmpFactsSource
from engineering_app.application.ports.nonconformity_repository import (
    NonconformityRepository,
)
from engineering_app.domain.nonconformity.errors import NcNotFoundError

_CONTEXT_MAX_PRODUCTS = 5


class ProductStructureSource(Protocol):
    async def fetch_product_structure(
        self,
        ctx: HomeSourceContext,
        *,
        code: str,
        max_depth: int = 6,
        page_size: int = 200,
    ) -> dict[str, Any]: ...


class GetNonconformityContextUseCase:
    """Contexto funcional de uma NC: OV oficial + estruturas dos produtos."""

    def __init__(
        self,
        repository: NonconformityRepository,
        facts_source: LmpFactsSource,
        product_source: ProductStructureSource,
    ) -> None:
        self._repository = repository
        self._facts = facts_source
        self._products = product_source

    async def execute(
        self,
        ctx: HomeSourceContext,
        *,
        record_id: str,
        max_depth: int = 6,
    ) -> dict[str, Any]:
        record = await asyncio.to_thread(self._repository.get_record, record_id)
        if record is None:
            raise NcNotFoundError(record_id)

        ov_status = "skipped"
        ov_data: dict[str, Any] | None = None
        sale_number = str(record.get("sale_number") or "").strip()
        if sale_number:
            fact = await self._facts.fetch_fact(
                ctx,
                sale_number=sale_number,
                start_date=None,
                end_date=None,
                branch=None,
                include=None,
            )
            ov_status = fact.status
            ov_data = fact.fact if fact.status == "available" else None
        else:
            ov_status = "not_linked"

        product_contexts: list[dict[str, Any]] = []
        for product in (record.get("products") or [])[:_CONTEXT_MAX_PRODUCTS]:
            code = str(product.get("product_code") or "").strip()
            if not code:
                continue
            structure = await self._products.fetch_product_structure(
                ctx, code=code, max_depth=max_depth
            )
            product_contexts.append(
                {
                    "product_code": code,
                    "product_description": product.get("product_description"),
                    "structure_status": structure.get("status"),
                    "structure": structure.get("data")
                    if structure.get("status") == "available"
                    else None,
                }
            )

        return {
            "nonconformity": record,
            "ov_status": ov_status,
            "ov": ov_data,
            "product_contexts": product_contexts,
            "product_contexts_truncated": len(record.get("products") or [])
            > _CONTEXT_MAX_PRODUCTS,
        }
