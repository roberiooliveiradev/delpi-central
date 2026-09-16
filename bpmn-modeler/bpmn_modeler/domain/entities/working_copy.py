from __future__ import annotations

from dataclasses import dataclass

from ..value_objects.canonical_bpmn_artifact import CanonicalBpmnArtifact


@dataclass(slots=True)
class WorkingCopy:
    """Current mutable canonical artifact for a model."""

    artifact: CanonicalBpmnArtifact

    def replace_artifact(self, artifact: CanonicalBpmnArtifact) -> None:
        self.artifact = artifact
