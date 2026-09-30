from __future__ import annotations

from bpmn_modeler.application.ports import BlankArtifactFactoryPort, IdGeneratorPort
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions id="{definitions_id}"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  targetNamespace="urn:delpi:bpmn-modeler"
  exporter="Minha DELPI BPMN Modeler" exporterVersion="1.0">
  <bpmn:process id="{process_id}" isExecutable="false"/>
  <bpmndi:BPMNDiagram id="{diagram_id}">
    <bpmndi:BPMNPlane id="{plane_id}" bpmnElement="{process_id}"/>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


class TemplateBlankArtifactFactory(BlankArtifactFactoryPort):
    """Frozen blank-artifact template (P3 section 14)."""

    def __init__(self, ids: IdGeneratorPort) -> None:
        self._ids = ids

    def new_blank_artifact(self) -> CanonicalBpmnArtifact:
        process_id = self._ids.new_bpmn_id("Process")
        return CanonicalBpmnArtifact(
            content=_TEMPLATE.format(
                definitions_id=self._ids.new_bpmn_id("Definitions"),
                process_id=process_id,
                diagram_id=self._ids.new_bpmn_id("BPMNDiagram"),
                plane_id=self._ids.new_bpmn_id("BPMNPlane"),
            )
        )
