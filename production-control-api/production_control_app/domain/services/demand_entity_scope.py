"""Escopo de entidade nos pedidos de venda do PCP.

A view TOTVS traz ``tipo_entidade`` = ``CLIENTE`` | ``FORNECEDOR``. O PCP
planeja demanda de **cliente**; remessa / venda para fornecedor (ex.: TRAMAR)
não entra na Demanda nem no card «a faturar até hoje».
"""

from __future__ import annotations

from typing import Any

SUPPLIER_ENTITY_TYPE = "FORNECEDOR"


def _entity_type(value: Any) -> str:
    return str(value or "").strip().upper()


def is_supplier_sales_entity(tipo_entidade: Any) -> bool:
    """True quando a linha é pedido de venda para fornecedor."""
    return _entity_type(tipo_entidade) == SUPPLIER_ENTITY_TYPE


def is_customer_sales_entity(tipo_entidade: Any) -> bool:
    """Aceita CLIENTE e valor vazio (legado); rejeita FORNECEDOR."""
    return not is_supplier_sales_entity(tipo_entidade)
