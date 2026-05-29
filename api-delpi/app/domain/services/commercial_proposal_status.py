from __future__ import annotations

from typing import Literal

ProposalStatusCategory = Literal["won", "lost", "open", "other"]

WON_STATUS_CODE = "9"
LOST_STATUS_CODES = frozenset({"8", "X"})

_STATUS_LABELS: dict[str, str] = {
    "1": "Aberta",
    "2": "Em andamento",
    "3": "Em negociação",
    "4": "Aguardando cliente",
    "5": "Aguardando interno",
    "6": "Suspensa",
    "7": "Cancelada",
    "8": "Perdida",
    "9": "Ganha",
    "X": "Perdida",
}


def normalize_status_code(value: str | None) -> str:
    return (value or "").strip()


def resolve_proposal_status_category(status_code: str | None) -> ProposalStatusCategory:
    code = normalize_status_code(status_code)
    if code == WON_STATUS_CODE:
        return "won"
    if code in LOST_STATUS_CODES:
        return "lost"
    if not code:
        return "other"
    if code in _STATUS_LABELS and code not in LOST_STATUS_CODES and code != WON_STATUS_CODE:
        return "open"
    return "other"


def resolve_proposal_status_label(status_code: str | None) -> str:
    code = normalize_status_code(status_code)
    if not code:
        return "Sem status"
    return _STATUS_LABELS.get(code, f"Status {code}")
