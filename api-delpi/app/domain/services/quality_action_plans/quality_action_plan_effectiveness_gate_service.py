from __future__ import annotations

from typing import Any

_MAX_LISTED_ACTIONS = 3
_DESCRIPTION_SNIPPET_LEN = 72

_STATUS_LABELS = {
    "pending": "Pendente",
    "in_progress": "Em andamento",
    "blocked": "Bloqueada",
    "overdue": "Atrasada",
}


def _action_snippet(action: dict[str, Any]) -> str:
    description = str(action.get("description") or "").strip()
    if not description:
        return str(action.get("id") or "Ação")
    if len(description) <= _DESCRIPTION_SNIPPET_LEN:
        return description
    return f"{description[:_DESCRIPTION_SNIPPET_LEN]}…"


def build_incomplete_plan_actions_message(actions: list[dict[str, Any]]) -> str:
    count = len(actions)
    if count == 0:
        return ""

    header = (
        f"Ainda há {count} ação(ões) não concluída(s). "
        "Revise a seção de ações e conclua ou cancele as pendências quando possível."
    )
    lines = [header]
    for action in actions[:_MAX_LISTED_ACTIONS]:
        status = str(action.get("status") or "pending")
        status_label = _STATUS_LABELS.get(status, status.replace("_", " "))
        lines.append(f"• {_action_snippet(action)} ({status_label})")
    if count > _MAX_LISTED_ACTIONS:
        lines.append(f"… e mais {count - _MAX_LISTED_ACTIONS}.")
    return "\n".join(lines)
