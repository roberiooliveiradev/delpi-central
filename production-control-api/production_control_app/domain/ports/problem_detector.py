"""Port — detector da Análise de problemas.

Cada detector responde por um tipo de exceção da fábrica. O serviço da área só
conhece este protocolo: nada de ``if detector_id ==`` em rota ou serviço.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class DetectorSummary:
    """Números do card. ``severity`` classifica o cartão inteiro."""

    count: int
    severity: str
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DetectorPage:
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    summary: DetectorSummary


class ProblemDetector(Protocol):
    @property
    def id(self) -> str:
        ...

    def summarize(self, *, branch: str) -> DetectorSummary:
        ...

    def collect(self, *, branch: str, page: int, page_size: int) -> DetectorPage:
        ...
