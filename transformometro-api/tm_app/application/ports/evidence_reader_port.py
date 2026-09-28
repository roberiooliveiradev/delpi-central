"""Read port for the Revision-scoped Evidence authority.

Always scoped to one revision — there is intentionally no global evidence
lookup, so callers cannot fall back across revisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EvidenceRef:
    """Minimal evidence descriptor as observed from its authority."""

    evidence_id: str
    revisao_id: str
    tipo: str
    nome_arquivo: str | None
    descricao: str | None


class EvidenceReaderPort(Protocol):
    def list_by_revision(self, revision_id: str) -> list[EvidenceRef]:
        """Currently-available (non-soft-deleted) evidence of one revision."""
        ...
