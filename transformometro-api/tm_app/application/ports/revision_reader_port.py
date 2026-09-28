"""Read port for the Revision contextual authority.

Application queries depend on this port — never on SQL or infrastructure.
Only the canonical fields the Diagnostic read surface needs are exposed;
the full revisoes row stays with its owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RevisionContext:
    """Canonical revision metadata observed from its own authority."""

    revision_id: str
    processo_id: str
    instancia_id: str | None
    versao_revisao: str
    cenario_tipo: str
    revisao_referencia_id: str | None


class RevisionReaderPort(Protocol):
    def get(self, revision_id: str) -> RevisionContext | None:
        """Resolve one revision; None when absent or soft-deleted."""
        ...
