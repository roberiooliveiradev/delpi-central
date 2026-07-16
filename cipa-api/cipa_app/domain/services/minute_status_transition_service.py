"""Máquina de estados das atas CIPA."""

from __future__ import annotations

EDITABLE_STATUSES = frozenset({"draft", "in_review"})
CONTENT_LOCKED_STATUSES = frozenset(
    {"awaiting_signatures", "partially_signed", "signed", "finalized", "cancelled"}
)
TERMINAL_STATUSES = frozenset({"finalized", "cancelled"})
DELETABLE_STATUSES = frozenset(
    {"draft", "in_review", "awaiting_signatures", "partially_signed", "cancelled"}
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"in_review", "awaiting_signatures", "cancelled"}),
    "in_review": frozenset({"draft", "awaiting_signatures", "cancelled"}),
    "awaiting_signatures": frozenset({"partially_signed", "signed", "in_review", "cancelled"}),
    "partially_signed": frozenset({"signed", "in_review", "cancelled"}),
    "signed": frozenset({"finalized", "cancelled"}),
    "finalized": frozenset(),
    "cancelled": frozenset(),
}


class MinuteStatusTransitionError(ValueError):
    """Transição de status inválida."""


class MinuteStatusTransitionService:
    @classmethod
    def can_edit_content(cls, status: str) -> bool:
        return status in EDITABLE_STATUSES

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        return status in TERMINAL_STATUSES

    @classmethod
    def can_delete(cls, status: str) -> bool:
        """Soft-delete permitido enquanto a ata ainda não está assinada/finalizada."""
        return status in DELETABLE_STATUSES

    @classmethod
    def requires_new_version_for_content_change(cls, status: str) -> bool:
        return status in CONTENT_LOCKED_STATUSES and status not in TERMINAL_STATUSES

    @classmethod
    def assert_transition(cls, from_status: str, to_status: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(from_status, frozenset())
        if to_status not in allowed:
            raise MinuteStatusTransitionError(
                f"Transição inválida: {from_status} → {to_status}."
            )

    @classmethod
    def status_after_signature_progress(
        cls,
        *,
        signed_count: int,
        required_count: int,
        refused: bool = False,
    ) -> str:
        if refused:
            return "in_review"
        if required_count <= 0:
            return "signed"
        if signed_count >= required_count:
            return "signed"
        if signed_count > 0:
            return "partially_signed"
        return "awaiting_signatures"
