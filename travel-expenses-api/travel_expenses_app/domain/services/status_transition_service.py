"""Travel report status machine. P0 HTTP only uses draft; future transitions live here."""

from __future__ import annotations

EDITABLE_STATUSES = frozenset({"draft", "returned"})
DELETABLE_STATUSES = frozenset({"draft"})
KNOWN_STATUSES = frozenset(
    {"draft", "submitted", "returned", "approved", "in_finance", "closed"}
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"submitted"}),
    "submitted": frozenset({"returned", "approved"}),
    "returned": frozenset({"draft", "submitted"}),
    "approved": frozenset({"in_finance", "returned"}),
    "in_finance": frozenset({"closed", "returned"}),
    "closed": frozenset(),
}


class TravelReportStatusTransitionError(ValueError):
    """Invalid status transition."""


class TravelReportStatusTransitionService:
    @classmethod
    def can_edit(cls, status: str) -> bool:
        return status in EDITABLE_STATUSES

    @classmethod
    def can_delete(cls, status: str) -> bool:
        return status in DELETABLE_STATUSES

    @classmethod
    def is_known(cls, status: str) -> bool:
        return status in KNOWN_STATUSES

    @classmethod
    def assert_transition(cls, from_status: str, to_status: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(from_status, frozenset())
        if to_status not in allowed:
            raise TravelReportStatusTransitionError(
                f"Transição inválida: {from_status} → {to_status}."
            )
