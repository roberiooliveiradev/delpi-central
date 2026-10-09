from __future__ import annotations

import json
from pathlib import Path

from lxml import etree

from .artifact import CanonicalBpmnArtifact
from .types import (
    BpmnArtifactValidationPort,
    InputSafetyEvaluationPort,
    InputSafetyEvidence,
    RuleSource,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)

from .intake import MAX_CANONICAL_UTF8_BYTES, MAX_INPUT_BYTES

NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS_BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"
NS_DC = "http://www.omg.org/spec/DD/20100524/DC"
NS_DI = "http://www.omg.org/spec/DD/20100524/DI"

NAMESPACES = {"bpmn": NS_BPMN, "bpmndi": NS_BPMNDI, "dc": NS_DC, "di": NS_DI}

_KNOWN_NAMESPACES = {
    NS_BPMN,
    NS_BPMNDI,
    NS_DC,
    NS_DI,
    "http://www.w3.org/2001/XMLSchema-instance",
    "http://www.w3.org/XML/1998/namespace",
    "",
}

FLOW_NODE_TYPES = {
    "task", "userTask", "serviceTask", "manualTask", "businessRuleTask",
    "scriptTask", "sendTask", "receiveTask", "callActivity", "subProcess",
    "adHocSubProcess", "transaction", "eventSubProcess",
    "startEvent", "endEvent", "intermediateCatchEvent",
    "intermediateThrowEvent", "boundaryEvent",
    "exclusiveGateway", "parallelGateway", "inclusiveGateway",
    "eventBasedGateway", "complexGateway",
    "implicitThrowEvent",
}

FLOW_ELEMENT_CONTAINERS = {
    "process", "subProcess", "adHocSubProcess", "transaction", "eventSubProcess",
}

ACTIVITY_TYPES = {
    "task", "userTask", "serviceTask", "manualTask", "businessRuleTask",
    "scriptTask", "sendTask", "receiveTask", "callActivity", "subProcess",
    "adHocSubProcess", "transaction",
}

PLANE_DEPICTABLE_TYPES = {"process", "collaboration", "subProcess", "participant"}

NON_INTERRUPTING_EVENT_DEFINITIONS = {
    "messageEventDefinition", "timerEventDefinition", "escalationEventDefinition",
    "signalEventDefinition", "conditionalEventDefinition",
}

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset()  # V1 registry is empty

XSD_DIR = Path(__file__).parent / "xsd"


def _issue(
    rule_id: str,
    stage: ValidationStage,
    source: RuleSource,
    severity: ValidationSeverity,
    message: str,
    reference: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        stage=stage,
        source=source,
        severity=severity,
        message=message,
        reference=reference,
    )


def _localname(tag: str) -> str:
    return etree.QName(tag).localname if isinstance(tag, str) else tag


def _namespace(tag: str) -> str:
    return etree.QName(tag).namespace or ""


def _element_id(element: etree._Element) -> str | None:
    return element.get("id")


def _ref(element: etree._Element) -> str | None:
    element_id = _element_id(element)
    return f"element:{element_id}" if element_id else None


class BpmnElementIndex:
    """Shared element index built once per validation."""

    def __init__(self, root: etree._Element) -> None:
        self.root = root
        self.by_id: dict[str, etree._Element] = {}
        self.duplicate_ids: list[str] = []
        for element in root.iter():
            element_id = _element_id(element)
            if element_id:
                if element_id in self.by_id:
                    self.duplicate_ids.append(element_id)
                else:
                    self.by_id[element_id] = element

    def resolve(self, qname_text: str | None) -> etree._Element | None:
        if not qname_text:
            return None
        local = qname_text.split(":")[-1]
        return self.by_id.get(local)

    def container_of(self, element: etree._Element) -> etree._Element | None:
        node = element.getparent()
        while node is not None:
            if (
                _namespace(node.tag) == NS_BPMN
                and _localname(node.tag) in FLOW_ELEMENT_CONTAINERS
            ):
                return node
            node = node.getparent()
        return None

    def process_of(self, element: etree._Element) -> etree._Element | None:
        node = element.getparent()
        while node is not None:
            if _namespace(node.tag) == NS_BPMN and _localname(node.tag) == "process":
                return node
            node = node.getparent()
        return None


class LxmlBpmnValidator(BpmnArtifactValidationPort, InputSafetyEvaluationPort):
    """Offline BPMN 2.0 validator: vendored OMG XSD + internal rule engine."""

    def __init__(self, xsd_dir: Path = XSD_DIR) -> None:
        self._verify_manifest(xsd_dir)
        try:
            schema_doc = etree.parse(str(xsd_dir / "BPMN20.xsd"))
            self._schema = etree.XMLSchema(schema_doc)
        except (etree.XMLSchemaParseError, OSError, etree.XMLSyntaxError) as exc:
            raise RuntimeError(f"XSD bundle failed to load: {exc}") from exc

    @staticmethod
    def _verify_manifest(xsd_dir: Path) -> None:
        import hashlib

        manifest_path = xsd_dir / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            digest = hashlib.sha256(
                (xsd_dir / entry["name"]).read_bytes()
            ).hexdigest()
            if digest != entry["sha256"]:
                raise RuntimeError(
                    f"XSD bundle integrity failure: {entry['name']}"
                )

    # ------------------------------------------------------------------ #

    def _new_parser(self) -> etree.XMLParser:
        return etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            load_dtd=False,
            dtd_validation=False,
            recover=False,
            huge_tree=False,
            ns_clean=False,
        )

    def evaluate(self, evidence: InputSafetyEvidence) -> ValidationReport:
        issues = list(self._input_safety_issues(evidence))
        return ValidationReport(
            evaluated_stages=frozenset({ValidationStage.INPUT_SAFETY}),
            not_evaluated_stages=frozenset(ValidationStage)
            - {ValidationStage.INPUT_SAFETY},
            issues=tuple(issues),
        )

    @staticmethod
    def _input_safety_issues(
        evidence: InputSafetyEvidence,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        stage = ValidationStage.INPUT_SAFETY

        def sec(rule_id: str, message: str) -> None:
            issues.append(
                _issue(rule_id, stage, RuleSource.SECURITY, ValidationSeverity.ERROR, message)
            )

        if evidence.original_byte_length > MAX_INPUT_BYTES:
            sec("SEC-SIZE-001", "input exceeds the maximum allowed size")
        if evidence.canonical_utf8_byte_length > MAX_CANONICAL_UTF8_BYTES:
            sec("SEC-SIZE-002", "canonical UTF-8 representation exceeds the maximum size")
        if evidence.dtd_detected:
            sec("SEC-DTD-001", "DOCTYPE/DTD declarations are not allowed")
        if evidence.external_entity_declarations_detected:
            sec("SEC-EXT-001", "external entity declarations are not allowed")
        if not evidence.depth_within_limit:
            sec("SEC-DEPTH-001", "input exceeds safe XML structure limits")
        if evidence.entity_expansion_beyond_builtins_detected:
            sec("SEC-ENT-001", "entity expansion beyond XML built-ins is not allowed")
        if not evidence.decode_succeeded:
            issues.append(
                _issue(
                    "SEC-ENC-001",
                    stage,
                    RuleSource.SECURITY,
                    ValidationSeverity.ERROR,
                    "input could not be decoded as XML text",
                )
            )
        return issues

    # ------------------------------------------------------------------ #

    def validate(
        self,
        artifact: CanonicalBpmnArtifact,
        evidence: InputSafetyEvidence | None = None,
    ) -> ValidationReport:
        evaluated: set[ValidationStage] = set()
        issues: list[ValidationIssue] = []

        if evidence is not None:
            evaluated.add(ValidationStage.INPUT_SAFETY)
            safety_issues = self._input_safety_issues(evidence)
            issues.extend(safety_issues)
            if any(i.severity is ValidationSeverity.ERROR for i in safety_issues):
                return self._report(evaluated, issues)

        root = self._parse(artifact, evaluated, issues)
        if root is None:
            return self._report(evaluated, issues)

        recognized = self._structure(root, evaluated, issues)
        if not recognized:
            return self._report(evaluated, issues)

        index = BpmnElementIndex(root)
        evaluated.add(ValidationStage.BPMN_SEMANTICS)
        issues.extend(self._semantics(root, index))
        evaluated.add(ValidationStage.BPMN_DI)
        issues.extend(self._di(root, index))
        evaluated.add(ValidationStage.PRODUCT_RULES)
        issues.extend(self._product(root, index))
        return self._report(evaluated, issues)

    def _report(
        self, evaluated: set[ValidationStage], issues: list[ValidationIssue]
    ) -> ValidationReport:
        evaluated_set = frozenset(evaluated)
        return ValidationReport(
            evaluated_stages=evaluated_set,
            not_evaluated_stages=frozenset(ValidationStage) - evaluated_set,
            issues=tuple(issues),
        )

    # ------------------------------------------------------------------ #

    def _parse(self, artifact, evaluated, issues) -> etree._Element | None:
        evaluated.add(ValidationStage.XML_WELL_FORMEDNESS)
        try:
            return etree.fromstring(
                artifact.content.encode("utf-8"), parser=self._new_parser()
            )
        except etree.XMLSyntaxError as exc:
            entry = exc.error_log.last_error
            message = str(exc).split("\n")[0]
            entry_text = (str(entry) + " " + message).lower()
            namespace_related = (
                "namespace prefix" in entry_text
                or "attribute" in entry_text and "not defined" in entry_text
                or "bound to namespace" in entry_text
            ) and "premature end" not in entry_text and "expected" not in entry_text
            rule_id = "XML-WF-NS-001" if namespace_related else "XML-WF-001"
            reference = (
                f"xml:{entry.line}:{entry.column}" if entry is not None else None
            )
            issues.append(
                _issue(
                    rule_id,
                    ValidationStage.XML_WELL_FORMEDNESS,
                    RuleSource.XML_W3C,
                    ValidationSeverity.ERROR,
                    "document is not well-formed XML",
                    reference,
                )
            )
            return None

    # ------------------------------------------------------------------ #

    def _structure(self, root, evaluated, issues) -> bool:
        evaluated.add(ValidationStage.BPMN_STRUCTURE)
        stage = ValidationStage.BPMN_STRUCTURE
        source = RuleSource.OMG_BPMN

        if _localname(root.tag) != "definitions":
            issues.append(
                _issue("BPMN-REC-001", stage, source, ValidationSeverity.ERROR,
                       "root element is not <definitions>", _ref(root))
            )
            return False
        if _namespace(root.tag) != NS_BPMN:
            issues.append(
                _issue("BPMN-REC-002", stage, source, ValidationSeverity.ERROR,
                       "root namespace is not the BPMN 2.0 model namespace",
                       _ref(root))
            )
            return False

        if not root.get("targetNamespace"):
            issues.append(
                _issue("BPMN-REC-004", stage, source, ValidationSeverity.ERROR,
                       "definitions lacks required targetNamespace", _ref(root))
            )

        has_process = root.find(f"{{{NS_BPMN}}}process") is not None
        has_collab = root.find(f"{{{NS_BPMN}}}collaboration") is not None
        if not has_process and not has_collab:
            issues.append(
                _issue("BPMN-REC-003", stage, source, ValidationSeverity.WARNING,
                       "definitions contains no process or collaboration",
                       _ref(root))
            )

        self._xsd_validate(root, issues)

        index = BpmnElementIndex(root)
        for dup in index.duplicate_ids:
            issues.append(
                _issue("BPMN-STRUCT-002", stage, source, ValidationSeverity.ERROR,
                       f"duplicated id '{dup}'", f"element:{dup}")
            )
        issues.extend(self._reference_rules(root, index, stage, source))
        return True

    def _xsd_validate(self, root, issues) -> None:
        self._schema.validate(root)
        for error in self._schema.error_log:
            issues.append(
                _issue(
                    "BPMN-STRUCT-001",
                    ValidationStage.BPMN_STRUCTURE,
                    RuleSource.OMG_BPMN,
                    ValidationSeverity.ERROR,
                    f"XSD violation: {error.message}",
                    f"xml:{error.line}:{error.column}",
                )
            )

    def _reference_rules(self, root, index: BpmnElementIndex, stage, source):
        issues: list[ValidationIssue] = []

        def emit(rule_id, message, element):
            issues.append(
                _issue(rule_id, stage, source, ValidationSeverity.ERROR, message, _ref(element))
            )

        for flow in root.iter(f"{{{NS_BPMN}}}sequenceFlow"):
            source_ref = flow.get("sourceRef")
            target_ref = flow.get("targetRef")
            source_el = index.resolve(source_ref)
            target_el = index.resolve(target_ref)
            if source_ref and source_el is None:
                emit("BPMN-STRUCT-010", "sequenceFlow sourceRef does not resolve", flow)
            if target_ref and target_el is None:
                emit("BPMN-STRUCT-011", "sequenceFlow targetRef does not resolve", flow)
            for endpoint, ref_el in (("sourceRef", source_el), ("targetRef", target_el)):
                if ref_el is not None and (
                    _namespace(ref_el.tag) != NS_BPMN
                    or _localname(ref_el.tag) not in FLOW_NODE_TYPES
                ):
                    emit("BPMN-STRUCT-012",
                         f"sequenceFlow {endpoint} is not a flow node", flow)

        for event in root.iter(f"{{{NS_BPMN}}}boundaryEvent"):
            attached = index.resolve(event.get("attachedToRef"))
            if attached is None or (
                _namespace(attached.tag) == NS_BPMN
                and _localname(attached.tag) not in ACTIVITY_TYPES
            ) or _namespace(attached.tag) != NS_BPMN:
                emit("BPMN-STRUCT-013",
                     "boundaryEvent attachedToRef does not resolve to an activity",
                     event)

        for participant in root.iter(f"{{{NS_BPMN}}}participant"):
            process_ref = participant.get("processRef")
            if process_ref and index.resolve(process_ref) is None:
                emit("BPMN-STRUCT-014",
                     "participant processRef does not resolve", participant)

        for lane in root.iter(f"{{{NS_BPMN}}}lane"):
            for ref_tag in ("flowNodeRef", "flowElementRef"):
                for ref in lane.findall(f"{{{NS_BPMN}}}{ref_tag}"):
                    if index.resolve(ref.text) is None:
                        emit("BPMN-STRUCT-015",
                             f"lane {ref_tag} does not resolve", lane)

        for message_flow in root.iter(f"{{{NS_BPMN}}}messageFlow"):
            for attr in ("sourceRef", "targetRef"):
                if index.resolve(message_flow.get(attr)) is None:
                    emit("BPMN-STRUCT-016",
                         f"messageFlow {attr} does not resolve", message_flow)

        association_types = (
            "association", "dataInputAssociation", "dataOutputAssociation",
        )
        for tag in association_types:
            for assoc in root.iter(f"{{{NS_BPMN}}}{tag}"):
                for attr in ("sourceRef", "targetRef"):
                    if index.resolve(assoc.get(attr)) is None:
                        emit("BPMN-STRUCT-017" if tag == "association" else "BPMN-STRUCT-018",
                             f"{tag} {attr} does not resolve", assoc)
        return issues

    # ------------------------------------------------------------------ #

    def _semantics(self, root, index: BpmnElementIndex) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        stage = ValidationStage.BPMN_SEMANTICS
        source = RuleSource.OMG_BPMN

        def emit(rule_id, severity, message, element):
            issues.append(_issue(rule_id, stage, source, severity, message, _ref(element)))

        for flow in root.iter(f"{{{NS_BPMN}}}sequenceFlow"):
            source_el = index.resolve(flow.get("sourceRef"))
            target_el = index.resolve(flow.get("targetRef"))
            if source_el is None or target_el is None:
                emit("BPMN-SEM-008", ValidationSeverity.WARNING,
                     "sequenceFlow has unresolved or missing endpoints", flow)
                continue
            source_container = index.container_of(source_el)
            target_container = index.container_of(target_el)
            if (
                source_container is not None
                and target_container is not None
                and source_container is not target_container
                and _localname(source_container.tag) == "process"
                and _localname(target_container.tag) == "process"
            ):
                emit("BPMN-SEM-001", ValidationSeverity.ERROR,
                     "sequenceFlow crosses process boundaries", flow)

        for message_flow in root.iter(f"{{{NS_BPMN}}}messageFlow"):
            source_el = index.resolve(message_flow.get("sourceRef"))
            target_el = index.resolve(message_flow.get("targetRef"))
            if source_el is None or target_el is None:
                continue
            same_process = (
                index.process_of(source_el) is not None
                and index.process_of(source_el) is index.process_of(target_el)
            )
            if same_process:
                emit("BPMN-SEM-002", ValidationSeverity.ERROR,
                     "messageFlow connects elements inside the same process",
                     message_flow)
            for endpoint in (source_el, target_el):
                if _localname(endpoint.tag) != "participant":
                    process = index.process_of(endpoint)
                    if (
                        process is not None
                        and _localname(endpoint.tag) in FLOW_NODE_TYPES
                        and self._participant_for_process(root, index, process)
                        is None
                    ):
                        emit("BPMN-SEM-007", ValidationSeverity.ERROR,
                             "messageFlow targets an internal element whose "
                             "process is not represented by a participant",
                             message_flow)
                        break

        for element in root.iter():
            if _namespace(element.tag) != NS_BPMN:
                continue
            default_ref = element.get("default")
            if default_ref:
                default_flow = index.resolve(default_ref)
                tag = _localname(element.tag)
                is_gateway_or_activity = tag in ACTIVITY_TYPES or tag.endswith("Gateway")
                if not is_gateway_or_activity:
                    emit("BPMN-SEM-003", ValidationSeverity.ERROR,
                         "default sequenceFlow declared on a non gateway/activity",
                         element)
                if default_flow is not None and default_flow.find(
                    f"{{{NS_BPMN}}}conditionExpression"
                ) is not None:
                    emit("BPMN-SEM-003", ValidationSeverity.ERROR,
                         "default sequenceFlow must not carry a conditionExpression",
                         element)

        for gateway in root.iter(f"{{{NS_BPMN}}}eventBasedGateway"):
            for outgoing in gateway.findall(f"{{{NS_BPMN}}}outgoing"):
                target_flow = index.resolve(outgoing.text)
                if target_flow is None or _localname(target_flow.tag) != "sequenceFlow":
                    continue
                target = index.resolve(target_flow.get("targetRef"))
                if target is not None and _localname(target.tag) not in (
                    "intermediateCatchEvent", "receiveTask",
                ):
                    emit("BPMN-SEM-004", ValidationSeverity.ERROR,
                         "eventBasedGateway outgoing must target an intermediate catch event or receive task",
                         gateway)

        for event in root.iter(f"{{{NS_BPMN}}}boundaryEvent"):
            if event.get("cancelActivity", "true") == "false":
                for definition in event:
                    name = _localname(definition.tag)
                    if name.endswith("EventDefinition") and name not in (
                        NON_INTERRUPTING_EVENT_DEFINITIONS
                    ):
                        emit("BPMN-SEM-005", ValidationSeverity.ERROR,
                             f"non-interrupting boundary event cannot use {name}",
                             event)

        link_throws: set[str] = set()
        link_catches: list[etree._Element] = []
        for thrower in root.iter(f"{{{NS_BPMN}}}intermediateThrowEvent"):
            for definition in thrower.iter(f"{{{NS_BPMN}}}linkEventDefinition"):
                if definition.get("name"):
                    link_throws.add(definition.get("name"))
        for catcher in root.iter(f"{{{NS_BPMN}}}intermediateCatchEvent"):
            for definition in catcher.iter(f"{{{NS_BPMN}}}linkEventDefinition"):
                link_catches.append((catcher, definition.get("name")))
        for catcher, name in link_catches:
            if name and name not in link_throws:
                emit("BPMN-SEM-006", ValidationSeverity.WARNING,
                     f"link catch event '{name}' has no matching throw event",
                     catcher)
        return issues

    @staticmethod
    def _participant_for_process(root, index, process):
        if process is None:
            return None
        process_id = _element_id(process)
        if not process_id:
            return None
        for participant in root.iter(f"{{{NS_BPMN}}}participant"):
            ref = participant.get("processRef") or ""
            if ref.split(":")[-1] == process_id:
                return participant
        return None

    # ------------------------------------------------------------------ #

    def _di(self, root, index: BpmnElementIndex) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        stage = ValidationStage.BPMN_DI
        source = RuleSource.OMG_BPMN_DI

        def emit(rule_id, severity, message, element=None, reference=None):
            issues.append(
                _issue(rule_id, stage, source, severity, message,
                       reference or (_ref(element) if element is not None else None))
            )

        diagrams = list(root.iter(f"{{{NS_BPMNDI}}}BPMNDiagram"))
        if not diagrams:
            emit("BPMNDI-001", ValidationSeverity.INFO,
                 "document contains no BPMNDiagram")
            return issues

        if len(diagrams) > 1:
            diagram_ids = ",".join(
                _element_id(d) or "?" for d in diagrams
            )
            emit("BPMNDI-008", ValidationSeverity.INFO,
                 f"document contains {len(diagrams)} BPMNDiagram elements ({diagram_ids})")

        depicted: set[str] = set()
        for diagram in diagrams:
            plane = diagram.find(f"{{{NS_BPMNDI}}}BPMNPlane")
            plane_ref = plane.get("bpmnElement") if plane is not None else None
            if plane is not None:
                resolved = index.resolve(plane_ref)
                if resolved is None or (
                    _namespace(resolved.tag) == NS_BPMN
                    and _localname(resolved.tag) not in PLANE_DEPICTABLE_TYPES
                ) or resolved is None or _namespace(resolved.tag) != NS_BPMN:
                    emit("BPMNDI-005", ValidationSeverity.ERROR,
                         "BPMNPlane bpmnElement does not resolve to a depictable element",
                         plane,
                         f"diagram:{_element_id(plane)}" if _element_id(plane) else None)

            for shape in plane.iter(f"{{{NS_BPMNDI}}}BPMNShape") if plane is not None else []:
                bpmn_ref = shape.get("bpmnElement")
                resolved = index.resolve(bpmn_ref)
                if resolved is None:
                    emit("BPMNDI-002", ValidationSeverity.ERROR,
                         "BPMNShape bpmnElement does not resolve", shape,
                         f"diagram:{_element_id(shape)}")
                elif bpmn_ref:
                    depicted.add(bpmn_ref.split(":")[-1])
                self._check_bounds(shape, emit)
                self._check_label(shape, emit)

            for edge in plane.iter(f"{{{NS_BPMNDI}}}BPMNEdge") if plane is not None else []:
                bpmn_ref = edge.get("bpmnElement")
                resolved = index.resolve(bpmn_ref)
                if resolved is None:
                    emit("BPMNDI-003", ValidationSeverity.ERROR,
                         "BPMNEdge bpmnElement does not resolve", edge,
                         f"diagram:{_element_id(edge)}")
                elif bpmn_ref:
                    depicted.add(bpmn_ref.split(":")[-1])
                waypoints = edge.findall(f"{{{NS_DI}}}waypoint")
                if len(waypoints) < 2:
                    emit("BPMNDI-004", ValidationSeverity.ERROR,
                         "BPMNEdge has fewer than two waypoints", edge,
                         f"diagram:{_element_id(edge)}")
                self._check_label(edge, emit)

        # BPMNDI-007: depictable elements missing depiction (per plane scope).
        depictable_tags = FLOW_NODE_TYPES | {
            "sequenceFlow", "messageFlow", "association", "participant", "lane",
            "dataObject", "dataObjectReference", "dataStoreReference",
            "textAnnotation", "group",
        }
        for diagram in diagrams:
            plane = diagram.find(f"{{{NS_BPMNDI}}}BPMNPlane")
            plane_ref = (plane.get("bpmnElement") or "").split(":")[-1] if plane is not None else None
            if not plane_ref:
                continue
            scope = index.resolve(plane_ref)
            if scope is None:
                continue
            depicted_in_plane = {
                (el.get("bpmnElement") or "").split(":")[-1]
                for el in plane.iter()
                if _namespace(el.tag) == NS_BPMNDI
                and _localname(el.tag) in ("BPMNShape", "BPMNEdge")
                and el.get("bpmnElement")
            }
            if _localname(scope.tag) == "collaboration":
                candidates = [
                    el for el in root.iter()
                    if _namespace(el.tag) == NS_BPMN
                    and _localname(el.tag) in ("participant", "messageFlow")
                ]
            else:
                candidates = [
                    el for el in scope.iter()
                    if _namespace(el.tag) == NS_BPMN
                    and _localname(el.tag) in depictable_tags
                ]
            missing = [
                _element_id(el) for el in candidates
                if _element_id(el) and _element_id(el) not in depicted_in_plane
            ]
            for element_id in sorted(missing):
                emit("BPMNDI-007", ValidationSeverity.INFO,
                     f"depictable element '{element_id}' has no shape/edge",
                     reference=f"element:{element_id}")
        return issues

    def _check_bounds(self, shape, emit) -> None:
        bounds = shape.find(f"{{{NS_DC}}}Bounds")
        if bounds is None:
            return
        try:
            width = float(bounds.get("width", "nan"))
            height = float(bounds.get("height", "nan"))
            float(bounds.get("x", "nan"))
            float(bounds.get("y", "nan"))
        except ValueError:
            emit("BPMNDI-006", ValidationSeverity.WARNING,
                 "dc:Bounds contains non-numeric coordinates", shape,
                 f"diagram:{_element_id(shape)}")
            return
        if width <= 0 or height <= 0:
            emit("BPMNDI-006", ValidationSeverity.WARNING,
                 "dc:Bounds has non-positive width/height", shape,
                 f"diagram:{_element_id(shape)}")

    def _check_label(self, owner, emit) -> None:
        label = owner.find(f"{{{NS_BPMNDI}}}BPMNLabel")
        if label is None:
            return
        if label.find(f"{{{NS_DC}}}Bounds") is None:
            emit("BPMNDI-009", ValidationSeverity.WARNING,
                 "BPMNLabel has no bounds", owner,
                 f"diagram:{_element_id(owner)}")

    # ------------------------------------------------------------------ #

    def _product(self, root, index: BpmnElementIndex) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        stage = ValidationStage.PRODUCT_RULES
        source = RuleSource.PRODUCT

        def emit(rule_id, severity, message, element=None, reference=None):
            issues.append(
                _issue(rule_id, stage, source, severity, message,
                       reference or (_ref(element) if element is not None else None))
            )

        for subprocess in root.iter(f"{{{NS_BPMN}}}subProcess"):
            flow_elements = [
                child for child in subprocess
                if _namespace(child.tag) == NS_BPMN
                and _localname(child.tag) in FLOW_NODE_TYPES | {"sequenceFlow"}
            ]
            if not flow_elements:
                emit("PROD-001", ValidationSeverity.WARNING,
                     "expanded subProcess contains no flow elements", subprocess)

        participant_ids_with_process = {
            (p.get("processRef") or "").split(":")[-1]
            for p in root.iter(f"{{{NS_BPMN}}}participant")
            if p.get("processRef")
        }
        for participant in root.iter(f"{{{NS_BPMN}}}participant"):
            if participant.get("processRef"):
                continue
            for diagram in root.iter(f"{{{NS_BPMNDI}}}BPMNDiagram"):
                for shape in diagram.iter(f"{{{NS_BPMNDI}}}BPMNShape"):
                    ref = (shape.get("bpmnElement") or "").split(":")[-1]
                    if ref == _element_id(participant) and shape.get(
                        "isExpanded"
                    ) == "true":
                        emit("PROD-002", ValidationSeverity.WARNING,
                             "black-box participant is depicted as expanded",
                             participant)

        self._extension_rules(root, emit)
        return issues

    def _extension_rules(self, root, emit) -> None:
        unknown_elements: dict[str, int] = {}
        for element in root.iter(f"{{{NS_BPMN}}}extensionElements"):
            for child in element:
                ns = _namespace(child.tag)
                if ns and ns not in _KNOWN_NAMESPACES:
                    key = f"{{{ns}}}{_localname(child.tag)}"
                    unknown_elements[key] = unknown_elements.get(key, 0) + 1
        for qname, count in sorted(unknown_elements.items()):
            emit("EXT-001", ValidationSeverity.INFO,
                 f"unknown extension element {qname} (x{count})")

        unknown_attrs: dict[str, int] = {}
        for element in root.iter():
            if _namespace(element.tag) not in _KNOWN_NAMESPACES:
                continue
            for attr in element.attrib:
                ns = _namespace(attr)
                if ns and ns not in _KNOWN_NAMESPACES:
                    key = f"{{{ns}}}{_localname(attr)}"
                    unknown_attrs[key] = unknown_attrs.get(key, 0) + 1
        for qname, count in sorted(unknown_attrs.items()):
            emit("EXT-002", ValidationSeverity.INFO,
                 f"unknown namespaced attribute {qname} (x{count})")

        for extension in root.iter(f"{{{NS_BPMN}}}extension"):
            definition = extension.get("definition", "")
            must = extension.get("mustUnderstand", "false")
            local = definition.split(":")[-1]
            uri = ""
            prefix, _, _ = definition.partition(":")
            if prefix and prefix != definition:
                uri = root.nsmap.get(prefix, "")
            qualified = f"{{{uri}}}{local}" if uri else local
            if must == "true" and qualified not in _SUPPORTED_EXTENSIONS:
                emit("EXT-003", ValidationSeverity.WARNING,
                     f"required extension '{definition}' is not supported",
                     reference=f"extension:{qualified}")
            else:
                emit("EXT-004", ValidationSeverity.INFO,
                     f"extension '{definition}' declared (mustUnderstand={must})",
                     reference=f"extension:{qualified}")
