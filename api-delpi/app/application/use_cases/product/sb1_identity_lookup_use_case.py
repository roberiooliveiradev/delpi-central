"""Lookup SB1 por identidade exata em lote — somente leitura."""

from __future__ import annotations

from typing import Any

from app.application.dto.product.sb1_identity_lookup_request import (
    Sb1IdentityLookupRequest,
)
from app.domain.services.product.sb1_identity_classifier import (
    classify_sb1_identity_pair,
    normalize_sb1_token,
)
from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
    ProductRepository,
)

MAX_ITEMS = 1000
ALLOWED_BRANCHES = frozenset({"01", "02"})


class Sb1IdentityLookupUseCase:
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self._repository = repository or ProductRepository()

    def execute(self, request: Sb1IdentityLookupRequest) -> dict[str, Any]:
        branch = str(request.branch or "").strip()
        if branch not in ALLOWED_BRANCHES:
            raise ValueError("branch inválida. Use '01' ou '02'.")
        if len(request.items) > MAX_ITEMS:
            raise ValueError(f"Limite de {MAX_ITEMS} itens por requisição excedido.")

        codes: list[str] = []
        references: list[str] = []
        seen_codes: set[str] = set()
        seen_refs: set[str] = set()
        for item in request.items:
            code = normalize_sb1_token(item.product_code)
            ref = normalize_sb1_token(item.customer_reference)
            if code and code not in seen_codes:
                seen_codes.add(code)
                codes.append(code)
            if ref and ref not in seen_refs:
                seen_refs.add(ref)
                references.append(ref)

        by_code_rows = self._repository.lookup_products_by_codes(codes)
        by_ref_rows = self._repository.lookup_products_by_customer_references(references)

        code_index: dict[str, dict[str, Any]] = {}
        for row in by_code_rows:
            key = normalize_sb1_token(row.get("product_code"))
            if key and key not in code_index:
                code_index[key] = row

        ref_index: dict[str, list[dict[str, Any]]] = {}
        for row in by_ref_rows:
            key = normalize_sb1_token(row.get("customer_reference"))
            if not key:
                continue
            ref_index.setdefault(key, []).append(row)

        results: list[dict[str, Any]] = []
        counts = {
            "confirmed": 0,
            "not_found": 0,
            "ambiguous": 0,
            "divergent": 0,
            "blocked": 0,
            "pending": 0,
        }
        for item in request.items:
            code = normalize_sb1_token(item.product_code)
            ref = normalize_sb1_token(item.customer_reference)
            classified = classify_sb1_identity_pair(
                product_code=code,
                customer_reference=ref,
                by_code=code_index.get(code) if code else None,
                by_reference=ref_index.get(ref, []) if ref else [],
                disambiguation_policy=request.disambiguation_policy,
            )
            status = str(classified["match_status"])
            if status in counts:
                counts[status] += 1
            results.append(
                {
                    "client_key": item.client_key,
                    **classified,
                }
            )

        return {
            "branch": branch,
            "read_only": True,
            "side_effects": False,
            "limits": {
                "max_items": MAX_ITEMS,
                "requested_items": len(request.items),
                "distinct_product_codes": len(codes),
                "distinct_customer_references": len(references),
            },
            "summary": counts,
            "results": results,
        }
