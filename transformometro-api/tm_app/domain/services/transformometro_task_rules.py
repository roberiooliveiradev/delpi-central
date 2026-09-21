from __future__ import annotations

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from tm_app.domain.entities.transformometro_task import TASK_STATUSES, TaskStatus

_USER_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
TITLE_MAX = 200
DESCRIPTION_MAX = 2000


def today_in_portal() -> date:
    return datetime.now(_SAO_PAULO).date()


def normalize_title(value: str | None) -> str:
    title = (value or "").strip()
    if not title:
        raise ValueError("O título da tarefa é obrigatório.")
    if len(title) > TITLE_MAX:
        raise ValueError(f"O título deve ter no máximo {TITLE_MAX} caracteres.")
    return title


def normalize_description(value: str | None) -> str | None:
    if value is None:
        return None
    description = value.strip()
    if not description:
        return None
    if len(description) > DESCRIPTION_MAX:
        raise ValueError(f"A descrição deve ter no máximo {DESCRIPTION_MAX} caracteres.")
    return description


def normalize_user_id(value: str | None, *, field: str) -> str:
    user_id = (value or "").strip()
    if not user_id or not _USER_ID_RE.match(user_id):
        raise ValueError(f"{field} precisa ser um identificador de usuário válido.")
    return user_id


def parse_due_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = str(value).strip()
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ValueError("Prazo inválido.") from exc


def is_overdue(status: TaskStatus, due: date | None, today: date | None = None) -> bool:
    if status != "pending" or due is None:
        return False
    return due < (today or today_in_portal())


def is_due_soon(status: TaskStatus, due: date | None, today: date | None = None) -> bool:
    if status != "pending" or due is None:
        return False
    current = today or today_in_portal()
    return current <= due <= date.fromordinal(current.toordinal() + 7)


def assert_status(value: str) -> TaskStatus:
    if value not in TASK_STATUSES:
        raise ValueError("Status de tarefa inválido.")
    return value  # type: ignore[return-value]


def assert_can_complete(status: TaskStatus) -> None:
    if status == "completed":
        raise ValueError("A tarefa já está concluída.")
    if status == "cancelled":
        raise ValueError("Tarefa cancelada não pode ser concluída.")


def assert_can_cancel(status: TaskStatus) -> None:
    if status == "cancelled":
        raise ValueError("A tarefa já está cancelada.")
    if status == "completed":
        raise ValueError("Tarefa concluída não pode ser cancelada.")


def assert_can_update(status: TaskStatus) -> None:
    if status != "pending":
        raise ValueError("Só tarefas pendentes podem ser editadas.")
