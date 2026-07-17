"""Escopo de fornecedores exibidos no estoque de segurança.

Fornecedores internos DELPI (cadastros usados para transferência entre
filiais da própria empresa) não são fornecedores de compra reais e ficam
fora da listagem de fornecedores vinculados.
"""

from __future__ import annotations

INTERNAL_TRANSFER_SUPPLIER_CODES: tuple[str, ...] = ("000052", "000972")


def internal_transfer_supplier_codes_sql() -> str:
    """Lista SQL (`'000052', '000972'`) para cláusulas NOT IN."""
    return ", ".join(f"'{code}'" for code in INTERNAL_TRANSFER_SUPPLIER_CODES)
