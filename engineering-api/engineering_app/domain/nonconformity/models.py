"""Entidades e value objects do domínio NC (framework-free).

Campos seguem o contrato legado E-NC-* para paridade semântica exata
com os consumidores existentes (doc 47 §8). PK é UUID (V002).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

NC_STATUSES: tuple[str, ...] = ("open", "in_progress", "done")

_VALID_STATUS_SET = frozenset(NC_STATUSES)


def normalize_nc_status(value: str | None) -> str | None:
    """Normaliza status para o enum fechado; inválido → None."""
    if value is None:
        return None
    text = str(value).strip().lower()
    return text if text in _VALID_STATUS_SET else None


@dataclass
class NcProduct:
    product_code: str
    product_description: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "product_code": self.product_code,
            "product_description": self.product_description,
        }


@dataclass
class NcActor:
    """Ator humano autenticado — trilha de auditoria do histórico."""

    user_id: str = "unknown"
    email: str | None = None
    name: str | None = None
    label: str | None = None


@dataclass
class Nonconformity:
    id: str | None
    status: str
    sale_number: str | None = None
    lmp_number: str | None = None
    customer_name: str | None = None
    occurrence_date: date | None = None
    launch_date: date | None = None
    last_revision_date: date | None = None
    executed_by: str | None = None
    released_by: str | None = None
    defect_description: str | None = None
    corrective_actions: str | None = None
    technical_opinion: str | None = None
    problem_tags: list[str] = field(default_factory=list)
    products: list[NcProduct] = field(default_factory=list)
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    registered_at: datetime | None = None

    def tracked_snapshot(self) -> dict[str, Any]:
        """Snapshot dos campos auditáveis para diff de histórico."""
        return {
            "status": self.status,
            "sale_number": self.sale_number,
            "lmp_number": self.lmp_number,
            "customer_name": self.customer_name,
            "occurrence_date": _iso(self.occurrence_date),
            "launch_date": _iso(self.launch_date),
            "last_revision_date": _iso(self.last_revision_date),
            "executed_by": self.executed_by,
            "released_by": self.released_by,
            "defect_description": self.defect_description,
            "corrective_actions": self.corrective_actions,
            "technical_opinion": self.technical_opinion,
            "problem_tags": list(self.problem_tags),
            "products": [item.as_dict() for item in self.products],
        }


@dataclass
class NcHistoryEvent:
    id: str | None
    nonconformity_id: str
    event_type: str
    actor_user_id: str = ""
    actor_email: str | None = None
    actor_name: str | None = None
    created_at: datetime | None = None
    changes: dict[str, Any] = field(default_factory=dict)


def _iso(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
