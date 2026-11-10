"""Regras dos planos de ação — validação, transições de status e vencimento."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from it_portal_app.domain.catalogs import (
    ACTION_PRIORITIES,
    ACTION_STATUSES,
    OPEN_ACTION_STATUSES,
)
from it_portal_app.domain.errors import ConflictError, ValidationError
from it_portal_app.domain.secret_guard import ensure_no_secret

TITLE_MAX = 160
RESPONSIBLE_MAX = 160
DESCRIPTION_MAX = 4000

ACTION_CODE_PREFIX = "PA-"

# Encerrados podem ser reabertos; nenhuma transição para o mesmo status.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"in_progress", "done", "cancelled"}),
    "in_progress": frozenset({"pending", "done", "cancelled"}),
    "done": frozenset({"in_progress"}),
    "cancelled": frozenset({"pending"}),
}


def format_action_code(seq: int) -> str:
    return f"{ACTION_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class ActionPlanFields:
    title: str
    description: str | None
    responsible: str | None
    priority: str
    due_date: date | None

    def as_dict(self) -> dict:
        return asdict(self)


ACTION_FIELD_NAMES = tuple(ActionPlanFields.__dataclass_fields__.keys())


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _parse_due_date(value: object, errors: dict) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(_clean(value))
    except ValueError:
        errors["due_date"] = "Prazo inválido (use AAAA-MM-DD)."
        return None


def build_action_plan_fields(raw: dict) -> ActionPlanFields:
    errors: dict[str, str] = {}

    title = _clean(raw.get("title"))
    if not title:
        errors["title"] = "Informe o título do plano de ação."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"Use no máximo {TITLE_MAX} caracteres."

    description = _clean(raw.get("description")) or None
    if description and len(description) > DESCRIPTION_MAX:
        errors["description"] = f"Use no máximo {DESCRIPTION_MAX} caracteres."

    responsible = _clean(raw.get("responsible")) or None
    if responsible and len(responsible) > RESPONSIBLE_MAX:
        errors["responsible"] = f"Use no máximo {RESPONSIBLE_MAX} caracteres."

    priority = _clean(raw.get("priority"))
    if priority not in ACTION_PRIORITIES:
        errors["priority"] = "Selecione a prioridade."

    due_date = _parse_due_date(raw.get("due_date"), errors)

    if errors:
        raise ValidationError(
            "invalid_action_plan",
            "Revise os campos destacados do plano de ação.",
            {"fields": errors},
        )

    ensure_no_secret("title", title)
    ensure_no_secret("description", description)

    return ActionPlanFields(
        title=title,
        description=description,
        responsible=responsible,
        priority=priority,
        due_date=due_date,
    )


def ensure_valid_status(status: str) -> str:
    if status not in ACTION_STATUSES:
        raise ValidationError(
            "invalid_action_status",
            "Status de plano de ação inválido.",
            {"fields": {"status": "Selecione um status válido."}},
        )
    return status


def ensure_transition(current: str, target: str) -> None:
    ensure_valid_status(target)
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise ConflictError(
            "invalid_status_transition",
            "Esta mudança de status não é permitida.",
            {"from": current, "to": target},
        )


def is_open(status: str) -> bool:
    return status in OPEN_ACTION_STATUSES


def is_overdue(status: str, due_date: date | None, today: date) -> bool:
    return is_open(status) and due_date is not None and due_date < today
