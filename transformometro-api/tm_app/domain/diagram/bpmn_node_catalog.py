"""Catálogo canônico de tipos BPMN suportados pelo flowchart_v1."""

from __future__ import annotations

from typing import Any, TypedDict


class BpmnNodeSpec(TypedDict, total=False):
    bpmn_tag: str
    bpmn_event_definition: str | None
    participates_in_flow: bool
    shape: str
    manual_task: bool


BPMN_NODE_CATALOG: dict[str, BpmnNodeSpec] = {
    "start": {"bpmn_tag": "startEvent", "participates_in_flow": True, "shape": "event_start"},
    "start_message": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "messageEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "start_timer": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "timerEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "start_signal": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "signalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "start_conditional": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "conditionalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "start_multiple": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "multipleEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "start_parallel": {
        "bpmn_tag": "startEvent",
        "bpmn_event_definition": "parallelMultipleEventDefinition",
        "participates_in_flow": True,
        "shape": "event_start",
    },
    "intermediate": {
        "bpmn_tag": "intermediateCatchEvent",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_message_catch": {
        "bpmn_tag": "intermediateCatchEvent",
        "bpmn_event_definition": "messageEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_timer": {
        "bpmn_tag": "intermediateCatchEvent",
        "bpmn_event_definition": "timerEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_signal_catch": {
        "bpmn_tag": "intermediateCatchEvent",
        "bpmn_event_definition": "signalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_conditional": {
        "bpmn_tag": "intermediateCatchEvent",
        "bpmn_event_definition": "conditionalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_link_catch": {
        "bpmn_tag": "intermediateCatchEvent",
        "bpmn_event_definition": "linkEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_catch",
    },
    "intermediate_message_throw": {
        "bpmn_tag": "intermediateThrowEvent",
        "bpmn_event_definition": "messageEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_throw",
    },
    "intermediate_signal_throw": {
        "bpmn_tag": "intermediateThrowEvent",
        "bpmn_event_definition": "signalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_throw",
    },
    "intermediate_link_throw": {
        "bpmn_tag": "intermediateThrowEvent",
        "bpmn_event_definition": "linkEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_throw",
    },
    "intermediate_escalation_throw": {
        "bpmn_tag": "intermediateThrowEvent",
        "bpmn_event_definition": "escalationEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_throw",
    },
    "intermediate_compensation_throw": {
        "bpmn_tag": "intermediateThrowEvent",
        "bpmn_event_definition": "compensateEventDefinition",
        "participates_in_flow": True,
        "shape": "event_intermediate_throw",
    },
    "end": {"bpmn_tag": "endEvent", "participates_in_flow": True, "shape": "event_end"},
    "end_message": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "messageEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_error": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "errorEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_terminate": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "terminateEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_signal": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "signalEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_escalation": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "escalationEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_cancel": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "cancelEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "end_compensation": {
        "bpmn_tag": "endEvent",
        "bpmn_event_definition": "compensateEventDefinition",
        "participates_in_flow": True,
        "shape": "event_end",
    },
    "decision": {"bpmn_tag": "exclusiveGateway", "participates_in_flow": True, "shape": "gateway"},
    "gateway_parallel": {"bpmn_tag": "parallelGateway", "participates_in_flow": True, "shape": "gateway"},
    "gateway_inclusive": {"bpmn_tag": "inclusiveGateway", "participates_in_flow": True, "shape": "gateway"},
    "gateway_complex": {"bpmn_tag": "complexGateway", "participates_in_flow": True, "shape": "gateway"},
    "gateway_event": {"bpmn_tag": "eventBasedGateway", "participates_in_flow": True, "shape": "gateway"},
    "process": {"bpmn_tag": "task", "participates_in_flow": True, "shape": "task", "manual_task": True},
    "task_user": {"bpmn_tag": "userTask", "participates_in_flow": True, "shape": "task"},
    "task_service": {"bpmn_tag": "serviceTask", "participates_in_flow": True, "shape": "task"},
    "task_manual": {"bpmn_tag": "manualTask", "participates_in_flow": True, "shape": "task", "manual_task": True},
    "task_script": {"bpmn_tag": "scriptTask", "participates_in_flow": True, "shape": "task"},
    "task_business_rule": {"bpmn_tag": "businessRuleTask", "participates_in_flow": True, "shape": "task"},
    "task_send": {"bpmn_tag": "sendTask", "participates_in_flow": True, "shape": "task"},
    "task_receive": {"bpmn_tag": "receiveTask", "participates_in_flow": True, "shape": "task"},
    "subprocess": {"bpmn_tag": "subProcess", "participates_in_flow": True, "shape": "activity_subprocess"},
    "call_activity": {"bpmn_tag": "callActivity", "participates_in_flow": True, "shape": "activity_call"},
    "subprocess_ad_hoc": {"bpmn_tag": "adHocSubProcess", "participates_in_flow": True, "shape": "activity_ad_hoc"},
    "subprocess_transaction": {"bpmn_tag": "transaction", "participates_in_flow": True, "shape": "activity_transaction"},
    "subprocess_event": {"bpmn_tag": "subProcess", "participates_in_flow": True, "shape": "activity_event_subprocess"},
    "document": {"bpmn_tag": "textAnnotation", "participates_in_flow": False, "shape": "artifact_document"},
    "data_object": {"bpmn_tag": "dataObjectReference", "participates_in_flow": False, "shape": "artifact_data_object"},
    "data": {"bpmn_tag": "dataStoreReference", "participates_in_flow": False, "shape": "artifact_data_store"},
    "comment": {"bpmn_tag": "textAnnotation", "participates_in_flow": False, "shape": "artifact_comment"},
    "group": {"bpmn_tag": "group", "participates_in_flow": False, "shape": "artifact_group"},
    "boundary_timer": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "timerEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_message": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "messageEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_error": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "errorEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_signal": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "signalEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_escalation": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "escalationEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_compensation": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "compensateEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_cancel": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "cancelEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
    "boundary_conditional": {
        "bpmn_tag": "boundaryEvent",
        "bpmn_event_definition": "conditionalEventDefinition",
        "participates_in_flow": True,
        "shape": "boundary",
    },
}

NODE_TYPES = frozenset(BPMN_NODE_CATALOG.keys())

EDGE_KINDS = frozenset({"sequence", "message_flow", "association"})

START_EVENT_TYPES = frozenset(
    node_type for node_type, spec in BPMN_NODE_CATALOG.items() if spec.get("shape") == "event_start"
)
END_EVENT_TYPES = frozenset(
    node_type for node_type, spec in BPMN_NODE_CATALOG.items() if spec.get("shape") == "event_end"
)
GATEWAY_TYPES = frozenset(
    node_type for node_type, spec in BPMN_NODE_CATALOG.items() if spec.get("shape") == "gateway"
)
NON_FLOW_NODE_TYPES = frozenset(
    node_type
    for node_type, spec in BPMN_NODE_CATALOG.items()
    if not spec.get("participates_in_flow", True)
)

BPMN_TAG_TO_DEFAULT_TYPE: dict[str, str] = {
    "startEvent": "start",
    "endEvent": "end",
    "intermediateCatchEvent": "intermediate",
    "intermediateThrowEvent": "intermediate_message_throw",
    "boundaryEvent": "boundary_timer",
    "exclusiveGateway": "decision",
    "parallelGateway": "gateway_parallel",
    "inclusiveGateway": "gateway_inclusive",
    "complexGateway": "gateway_complex",
    "eventBasedGateway": "gateway_event",
    "task": "process",
    "userTask": "task_user",
    "serviceTask": "task_service",
    "manualTask": "task_manual",
    "scriptTask": "task_script",
    "businessRuleTask": "task_business_rule",
    "sendTask": "task_send",
    "receiveTask": "task_receive",
    "subProcess": "subprocess",
    "callActivity": "call_activity",
    "adHocSubProcess": "subprocess_ad_hoc",
    "transaction": "subprocess_transaction",
    "textAnnotation": "comment",
    "dataObjectReference": "data_object",
    "dataStoreReference": "data",
    "group": "group",
}

EVENT_DEFINITION_SUFFIX: dict[str, str] = {
    "messageEventDefinition": "message",
    "timerEventDefinition": "timer",
    "signalEventDefinition": "signal",
    "conditionalEventDefinition": "conditional",
    "errorEventDefinition": "error",
    "escalationEventDefinition": "escalation",
    "compensateEventDefinition": "compensation",
    "cancelEventDefinition": "cancel",
    "terminateEventDefinition": "terminate",
    "linkEventDefinition": "link",
    "multipleEventDefinition": "multiple",
    "parallelMultipleEventDefinition": "parallel",
}


def catalog_spec(node_type: str) -> BpmnNodeSpec:
    return BPMN_NODE_CATALOG.get(node_type, BPMN_NODE_CATALOG["process"])


def normalize_node_type(node_type: str) -> str:
    return node_type if node_type in NODE_TYPES else "process"
