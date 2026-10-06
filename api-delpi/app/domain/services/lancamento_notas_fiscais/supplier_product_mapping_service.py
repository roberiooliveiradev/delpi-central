"""Resolução Produto x Fornecedor. A SA5 é compartilhada: a filial não entra na chave.

A combinação é fornecedor + loja + código do fornecedor. Vários registros com o
mesmo produto interno continuam mapeados. Dois produtos internos distintos
ficam ambíguos e nenhum deles é escolhido.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupplierProductResolution:
    mapping_status: str
    internal_product_code: str | None
    internal_product_description: str | None


def resolve_supplier_product_codes(
    supplier_product_codes: list[str],
    rows: list[dict[str, str]],
) -> dict[str, SupplierProductResolution]:
    grouped: dict[str, dict[str, str | None]] = {}
    for row in rows:
        supplier_code = str(row.get("supplier_product_code") or "")
        internal_code = str(row.get("internal_product_code") or "")
        if not supplier_code or not internal_code:
            continue
        description = str(row.get("internal_product_description") or "") or None
        products = grouped.setdefault(supplier_code, {})
        current = products.get(internal_code)
        if internal_code not in products or (not current and description):
            products[internal_code] = description

    resolved: dict[str, SupplierProductResolution] = {}
    for code in supplier_product_codes:
        products = grouped.get(code) or {}
        if len(products) == 1:
            internal_code, description = next(iter(products.items()))
            resolved[code] = SupplierProductResolution(
                mapping_status="mapped",
                internal_product_code=internal_code,
                internal_product_description=description,
            )
        elif len(products) > 1:
            resolved[code] = SupplierProductResolution(
                mapping_status="ambiguous",
                internal_product_code=None,
                internal_product_description=None,
            )
        else:
            resolved[code] = SupplierProductResolution(
                mapping_status="unmapped",
                internal_product_code=None,
                internal_product_description=None,
            )
    return resolved
