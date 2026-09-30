"""Administração do catálogo MES de motivos de parada (contrato S2S).

Fatos administráveis: ``label``, ``category``, ``requires_note``,
``sort_order``, ``active``. ``code`` é identidade técnica imutável — criado
uma vez, nunca renomeado. Não existe exclusão física: desativação preserva
``downtime_events.reason_code`` e o histórico industrial.

``setup`` é motivo protegido: a parada automática sem peça contada usa esse
código como classificação inicial — desativá-lo degradaria a regra, então
``active=false`` sobre ``setup`` é rejeitado com conflito explícito.

Os campos OEE (``default_planned``, ``default_counts_as_availability_loss``)
ficam fora da administração nesta etapa — o banco preserva os valores atuais.
"""

from __future__ import annotations

import re
from typing import Any

from production_control_app.domain.errors import (
    DowntimeReasonConflict,
    DowntimeReasonNotFound,
    InvalidDowntimeReason,
)
from production_control_app.domain.ports.downtime_reason_repository import (
    DowntimeReasonRepositoryPort,
)

_CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_CODE_MAX = 40
_LABEL_MAX = 120
_CATEGORY_MAX = 40

# Motivos que regras automáticas do próprio MES dependem por identidade estável.
PROTECTED_REASON_CODES = frozenset({"setup"})


class MesDowntimeReasonAdminService:
    def __init__(self, *, reasons: DowntimeReasonRepositoryPort) -> None:
        self._reasons = reasons

    def list_reasons(self) -> dict[str, Any]:
        return {"items": [self._view(row) for row in self._reasons.list_all()]}

    def create_reason(
        self,
        *,
        code: Any,
        label: Any,
        category: Any,
        requires_note: Any,
        sort_order: Any,
    ) -> dict[str, Any]:
        row = self._reasons.create(
            code=_normalize_code(code),
            label=_normalize_label(label),
            category=_normalize_category(category),
            requires_note=_normalize_requires_note(requires_note),
            sort_order=_normalize_sort_order(sort_order),
        )
        return self._view(row)

    def update_reason(
        self,
        code: Any,
        *,
        label: Any,
        category: Any,
        requires_note: Any,
        sort_order: Any,
    ) -> dict[str, Any]:
        normalized = _normalize_code(code)
        row = self._reasons.update(
            normalized,
            label=_normalize_label(label),
            category=_normalize_category(category),
            requires_note=_normalize_requires_note(requires_note),
            sort_order=_normalize_sort_order(sort_order),
        )
        if row is None:
            raise DowntimeReasonNotFound(f"Motivo de parada '{normalized}' não existe.")
        return self._view(row)

    def set_reason_active(self, code: Any, *, active: Any) -> dict[str, Any]:
        normalized = _normalize_code(code)
        flag = _normalize_active(active)
        if normalized in PROTECTED_REASON_CODES and not flag:
            raise DowntimeReasonConflict(
                f"O motivo '{normalized}' é protegido: a classificação automática "
                "de parada sem peças depende dele ativo."
            )
        row = self._reasons.set_active(normalized, active=flag)
        if row is None:
            raise DowntimeReasonNotFound(f"Motivo de parada '{normalized}' não existe.")
        return self._view(row)

    @staticmethod
    def _view(row: dict[str, Any]) -> dict[str, Any]:
        created = row.get("created_at")
        updated = row.get("updated_at")
        return {
            "code": row["code"],
            "label": row["label"],
            "category": row["category"],
            "requiresNote": bool(row.get("requires_note")),
            "active": bool(row.get("active")),
            "sortOrder": int(row.get("sort_order") or 0),
            "createdAt": created.isoformat() if hasattr(created, "isoformat") else created,
            "updatedAt": updated.isoformat() if hasattr(updated, "isoformat") else updated,
        }


def _normalize_code(value: Any) -> str:
    code = str(value or "").strip().lower()
    if not code:
        raise InvalidDowntimeReason("O código do motivo é obrigatório.")
    if len(code) > _CODE_MAX:
        raise InvalidDowntimeReason(f"O código do motivo excede {_CODE_MAX} caracteres.")
    if not _CODE_PATTERN.match(code):
        raise InvalidDowntimeReason(
            "O código do motivo aceita apenas minúsculas, números e '_' "
            "(ex.: raw_material, machine_failure)."
        )
    return code


def _normalize_label(value: Any) -> str:
    label = str(value or "").strip()
    if not label:
        raise InvalidDowntimeReason("O rótulo do motivo é obrigatório.")
    if len(label) > _LABEL_MAX:
        raise InvalidDowntimeReason(f"O rótulo do motivo excede {_LABEL_MAX} caracteres.")
    return label


def _normalize_category(value: Any) -> str:
    category = str(value or "").strip().lower()
    if not category:
        raise InvalidDowntimeReason("A categoria do motivo é obrigatória.")
    if len(category) > _CATEGORY_MAX:
        raise InvalidDowntimeReason(
            f"A categoria do motivo excede {_CATEGORY_MAX} caracteres."
        )
    return category


def _normalize_requires_note(value: Any) -> bool:
    if not isinstance(value, bool):
        raise InvalidDowntimeReason("requiresNote deve ser booleano.")
    return value


def _normalize_sort_order(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidDowntimeReason("sortOrder deve ser inteiro.")
    if value < 0:
        raise InvalidDowntimeReason("sortOrder não pode ser negativo.")
    return value


def _normalize_active(value: Any) -> bool:
    if not isinstance(value, bool):
        raise InvalidDowntimeReason("active deve ser booleano.")
    return value
