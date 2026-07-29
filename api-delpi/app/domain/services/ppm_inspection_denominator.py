"""Regras de negócio do denominador PPM — produção apontada no CT de inspeção final.

Constantes de CT / tipos vivem no módulo de apontamentos (fonte única).
"""

from app.domain.production.production_appointments.production_appointments_scope import (
    CT_INSPECAO_NOME_SQL_LIKE,
    DEFAULT_PRODUCED_PRODUCT_TYPES,
)

PPM_PRODUCED_B1_TIPOS: frozenset[str] = DEFAULT_PRODUCED_PRODUCT_TYPES

__all__ = [
    "CT_INSPECAO_NOME_SQL_LIKE",
    "PPM_PRODUCED_B1_TIPOS",
    "is_eligible_product_type",
    "sql_b1_tipo_in_clause",
]


def is_eligible_product_type(tipo: str | None) -> bool:
    """Retorna True se o tipo SB1010 entra no total produzido do PPM."""
    return (tipo or "").strip().upper() in PPM_PRODUCED_B1_TIPOS


def sql_b1_tipo_in_clause() -> str:
    tipos = ", ".join(f"'{tipo}'" for tipo in sorted(PPM_PRODUCED_B1_TIPOS))
    return f"({tipos})"
