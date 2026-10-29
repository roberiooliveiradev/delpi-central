"""BPMN auto-layout port — server-side execution of the CANONICAL
Organizar pipeline (plugins/bpmn-editor/src/layout, elkjs).

The port exists so governed write capabilities can organize BPMN-DI
without depending on the concrete Node/subprocess adapter. Layout
touches ONLY presentation geometry — BPMN semantics are preserved by
construction (the pipeline strips and rebuilds BPMN-DI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class BpmnLayoutError(RuntimeError):
    """Layout computation failed (invalid input, engine failure or
    infrastructure error). Callers may fall back to the unorganized
    candidate per product policy."""


@dataclass(frozen=True)
class BpmnLayoutResult:
    """Outcome of organizing a BPMN XML document."""

    xml: str
    """Final XML with rebuilt BPMN-DI (semantics identical to input)."""
    changed: bool
    """True when computed geometry differs from the input's DI beyond
    the pipeline's tolerance — False means the diagram was already
    organized (idempotent no-op)."""
    moved_elements: int = 0


class BpmnLayoutPort(Protocol):
    """Canonical Organizar algorithm, executed server-side."""

    def organize(self, xml: str) -> BpmnLayoutResult:
        """Return the BPMN XML with organized BPMN-DI geometry.

        Raises BpmnLayoutError on input/engine/infrastructure failure —
        the input document is never mutated.
        """
        ...
