"""Decide when to notify the request creator via Portal (outbox → Core).

Gates are derived from workflow journey outcomes — no type_code branching.
"""

from __future__ import annotations

from typing import Any

from requests_app.domain.services.journey_progress_service import resolve_journey_progress

_CREATOR_GATE_OUTCOMES = frozenset(
    {"waiting_requester", "succeeded", "rejected", "cancelled"}
)


def should_notify_creator_on_transition(
    *,
    workflow: dict[str, Any] | None,
    from_status: str | None,
    to_status: str,
    actor_user_id: str,
    owner_user_id: str,
) -> bool:
    """Return True when the Portal bell should notify the creator."""
    actor = str(actor_user_id or "").strip()
    owner = str(owner_user_id or "").strip()
    if not actor or not owner or actor == owner:
        return False
    destination = str(to_status or "").strip()
    if not destination:
        return False

    to_progress = resolve_journey_progress(workflow, status=destination)
    if to_progress is None:
        return _fallback_without_journey(
            workflow=workflow,
            from_status=from_status,
            to_status=destination,
        )

    outcome = str(to_progress.get("outcome") or "")
    if outcome in _CREATOR_GATE_OUTCOMES:
        return True

    to_stage = str(to_progress.get("current_stage_id") or "")
    from_progress = (
        resolve_journey_progress(workflow, status=str(from_status))
        if from_status
        else None
    )
    from_stage = (
        str(from_progress.get("current_stage_id") or "") if from_progress else ""
    )
    if (
        to_stage == "service"
        and outcome == "in_progress"
        and from_stage != "service"
    ):
        return True
    return False


def _fallback_without_journey(
    *,
    workflow: dict[str, Any] | None,
    from_status: str | None,
    to_status: str,
) -> bool:
    terminals = {
        str(item).strip()
        for item in ((workflow or {}).get("terminalStatuses") or [])
        if str(item).strip()
    }
    initial = str((workflow or {}).get("initialStatus") or "submitted").strip()
    if to_status in terminals:
        return True
    if to_status == "needs_information":
        return True
    if to_status == "in_progress" and str(from_status or "").strip() == initial:
        return True
    return False


def resolve_creator_gate_copy(
    *,
    workflow: dict[str, Any] | None,
    to_status: str,
    request_number: str,
    actor_name: str,
) -> tuple[str, str, str]:
    """Return (title, message, notification_type) for a creator gate."""
    progress = resolve_journey_progress(workflow, status=to_status)
    outcome = str((progress or {}).get("outcome") or "")
    summary = (progress or {}).get("summary")
    number = (request_number or "").strip() or "Solicitação"
    actor = (actor_name or "").strip() or "alguém"

    if outcome == "waiting_requester":
        if to_status == "awaiting_requester_confirmation":
            title = "Confirme o atendimento"
            detail = (
                str(summary).strip()
                if summary
                else "A nota foi registrada. Confirme se o pedido foi atendido."
            )
            return title, f"{number}: {detail}", "warning"
        title = "Aguardando sua informação"
        detail = str(summary).strip() if summary else "Informações adicionais foram pedidas."
        return title, f"{number}: {detail}", "warning"
    if outcome == "succeeded":
        return "Solicitação concluída", f"{number} foi concluída por {actor}.", "success"
    if outcome == "rejected":
        return "Solicitação rejeitada", f"{number} foi rejeitada por {actor}.", "error"
    if outcome == "cancelled":
        return "Solicitação cancelada", f"{number} foi cancelada por {actor}.", "warning"
    if outcome == "in_progress" or to_status == "in_progress":
        return (
            "Atendimento iniciado",
            f"{number} entrou em atendimento por {actor}.",
            "info",
        )
    if to_status == "needs_information":
        return (
            "Aguardando sua informação",
            f"{number}: informações adicionais foram pedidas.",
            "warning",
        )
    if to_status in {"completed", "rejected", "cancelled"}:
        labels = {
            "completed": ("Solicitação concluída", "success"),
            "rejected": ("Solicitação rejeitada", "error"),
            "cancelled": ("Solicitação cancelada", "warning"),
        }
        title, variant = labels[to_status]
        return title, f"{number} atualizada por {actor}.", variant
    return "Solicitação atualizada", f"{number} — {to_status} por {actor}.", "info"
