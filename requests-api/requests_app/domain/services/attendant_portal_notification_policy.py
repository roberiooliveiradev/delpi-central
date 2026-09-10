"""Decide when to notify the attending processor (assignee) via Portal outbox.

Recipient is the active processor assignment — not every user with `.process`.
"""

from __future__ import annotations


def should_notify_assignee(
    *,
    actor_user_id: str | None,
    assignee_user_id: str | None,
) -> bool:
    """True when there is an assignee distinct from the actor."""
    actor = str(actor_user_id or "").strip()
    assignee = str(assignee_user_id or "").strip()
    if not actor or not assignee:
        return False
    return actor != assignee


def resolve_assignee_comment_copy(
    *,
    request_number: str,
    actor_name: str,
) -> tuple[str, str, str]:
    number = (request_number or "").strip() or "Solicitação"
    actor = (actor_name or "").strip() or "alguém"
    return (
        "Novo comentário",
        f"{actor} comentou em {number}.",
        "info",
    )


def resolve_assignee_transition_copy(
    *,
    request_number: str,
    actor_name: str,
    to_status: str,
    action: str | None = None,
) -> tuple[str, str, str]:
    number = (request_number or "").strip() or "Solicitação"
    actor = (actor_name or "").strip() or "alguém"
    action_key = str(action or "").strip().lower()
    status = str(to_status or "").strip()

    if action_key == "resubmit":
        return (
            "Solicitação reenviada",
            f"{number} foi reenviada por {actor}.",
            "info",
        )
    if action_key in {"confirm_fulfillment", "confirm"}:
        return (
            "Atendimento confirmado",
            f"{number}: o solicitante confirmou o atendimento.",
            "success",
        )
    if action_key in {"reject_fulfillment", "return"}:
        return (
            "Devolvida para correção",
            f"{number} foi devolvida por {actor}.",
            "warning",
        )
    if action_key == "edit":
        return (
            "Dados atualizados",
            f"{number}: {actor} atualizou os dados da solicitação.",
            "info",
        )
    if status:
        return (
            "Solicitação atualizada",
            f"{number} — {status} por {actor}.",
            "info",
        )
    return "Solicitação atualizada", f"{number} atualizada por {actor}.", "info"


def resolve_queue_created_copy(*, request_number: str, type_name: str | None = None) -> tuple[str, str, str]:
    number = (request_number or "").strip() or "Solicitação"
    label = (type_name or "").strip()
    if label:
        return "Nova solicitação na fila", f"{number} ({label}) aguarda atendimento.", "info"
    return "Nova solicitação na fila", f"{number} aguarda atendimento.", "info"
