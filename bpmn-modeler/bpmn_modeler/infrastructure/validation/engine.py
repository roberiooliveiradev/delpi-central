"""Re-export compat — engine offline vive em ``shared/bpmn_validation`` (G7)."""

from bpmn_validation.engine import NAMESPACES, LxmlBpmnValidator

__all__ = ["LxmlBpmnValidator", "NAMESPACES"]
