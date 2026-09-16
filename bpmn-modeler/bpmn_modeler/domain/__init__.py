"""Domain model for the BPMN Modeler bounded context."""

from .entities.model import Model
from .entities.working_copy import WorkingCopy
from .value_objects.canonical_bpmn_artifact import CanonicalBpmnArtifact

__all__ = ["CanonicalBpmnArtifact", "Model", "WorkingCopy"]
