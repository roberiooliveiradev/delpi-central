"""Família de OP Protheus — prefixo + sequência (sufixo 001 = mãe)."""

from __future__ import annotations

from app.domain.production.production_appointments.production_appointments_scope import (
    MOTHER_OP_SUFFIX,
)


class ProductionAppointmentsOpFamilyService:
    """Deriva prefixo de família a partir de ``H6_OP`` / ``C2_OP`` (tudo antes da sequência)."""

    @classmethod
    def normalize_op(cls, production_order: str | None) -> str:
        return str(production_order or "").strip()

    @classmethod
    def is_mother_op(cls, production_order: str | None) -> bool:
        op = cls.normalize_op(production_order)
        suffix_len = len(MOTHER_OP_SUFFIX)
        return bool(op) and len(op) > suffix_len and op.endswith(MOTHER_OP_SUFFIX)

    @classmethod
    def family_prefix(cls, production_order: str | None) -> str:
        op = cls.normalize_op(production_order)
        suffix_len = len(MOTHER_OP_SUFFIX)
        if len(op) <= suffix_len:
            raise ValueError(
                "OP inválida para família: informe o código completo "
                f"(mínimo {suffix_len + 1} caracteres)."
            )
        return op[:-suffix_len]
