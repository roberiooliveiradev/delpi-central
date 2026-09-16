from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CanonicalBpmnArtifact:
    """Opaque BPMN XML payload owned by the BPMN Modeler.

    Construction does not parse or establish XML, BPMN, or BPMN-DI validity.
    Validation belongs to the dedicated validation boundary.
    """

    content: str
