"""FX-* fixture corpus for the 47-rule validation catalog.

Each entry: (input_bytes_or_str, expected_state, expected_rule_ids_subset)
States match RecognitionState values; the rule subset must be present.
"""

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" '
    f'xmlns:bpmndi="{BPMNDI_NS}" xmlns:dc="{DC_NS}" xmlns:di="{DI_NS}" '
    'id="Definitions_1" targetNamespace="urn:test" '
    'exporter="test" exporterVersion="1.0">\n'
)
FOOTER = "</bpmn:definitions>"

FX_VALID_001 = HEADER + """
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:task id="Task_1"/>
    <bpmn:task id="Task_2"/>
    <bpmn:endEvent id="End_1"/>
    <bpmn:sequenceFlow id="F1" sourceRef="Start_1" targetRef="Task_1"/>
    <bpmn:sequenceFlow id="F2" sourceRef="Task_1" targetRef="Task_2"/>
    <bpmn:sequenceFlow id="F3" sourceRef="Task_2" targetRef="End_1"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="D1">
    <bpmndi:BPMNPlane id="P1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S1" bpmnElement="Start_1"><dc:Bounds x="10" y="10" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S2" bpmnElement="Task_1"><dc:Bounds x="100" y="10" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S3" bpmnElement="Task_2"><dc:Bounds x="250" y="10" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S4" bpmnElement="End_1"><dc:Bounds x="400" y="10" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E1" bpmnElement="F1"><di:waypoint x="46" y="28"/><di:waypoint x="100" y="50"/></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E2" bpmnElement="F2"><di:waypoint x="200" y="50"/><di:waypoint x="250" y="50"/></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E3" bpmnElement="F3"><di:waypoint x="350" y="50"/><di:waypoint x="400" y="28"/></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
""" + FOOTER

FX_VALID_002 = HEADER + """
  <bpmn:collaboration id="Collab_1">
    <bpmn:participant id="Pool_A" processRef="Process_A"/>
    <bpmn:participant id="Pool_B"/>
    <bpmn:messageFlow id="MF1" sourceRef="Pool_B" targetRef="Task_A"/>
  </bpmn:collaboration>
  <bpmn:process id="Process_A" isExecutable="false">
    <bpmn:laneSet id="LS1">
      <bpmn:lane id="Lane_1"><bpmn:flowNodeRef>Task_A</bpmn:flowNodeRef>
        <bpmn:childLaneSet id="CLS1"><bpmn:lane id="Lane_1a"/></bpmn:childLaneSet>
      </bpmn:lane>
    </bpmn:laneSet>
    <bpmn:task id="Task_A"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="D1">
    <bpmndi:BPMNPlane id="P1" bpmnElement="Collab_1">
      <bpmndi:BPMNShape id="PS_A" bpmnElement="Pool_A" isExpanded="true"><dc:Bounds x="10" y="10" width="500" height="200"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="PS_B" bpmnElement="Pool_B"><dc:Bounds x="10" y="250" width="500" height="100"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="LS_1" bpmnElement="Lane_1"><dc:Bounds x="40" y="10" width="470" height="200"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="TS_A" bpmnElement="Task_A"><dc:Bounds x="100" y="50" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="ME1" bpmnElement="MF1"><di:waypoint x="150" y="250"/><di:waypoint x="150" y="130"/></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
""" + FOOTER

FX_NODI_001 = HEADER + """
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:task id="Task_1"/>
    <bpmn:sequenceFlow id="F1" sourceRef="Start_1" targetRef="Task_1"/>
  </bpmn:process>
""" + FOOTER

FX_NODI_002 = HEADER + """
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="Start_1"/>
    <bpmn:task id="Task_1"/>
    <bpmn:sequenceFlow id="F1" sourceRef="Start_1" targetRef="Task_1"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="D1">
    <bpmndi:BPMNPlane id="P1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S1" bpmnElement="Task_1"><dc:Bounds x="100" y="10" width="100" height="80"/></bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
""" + FOOTER

FX_BADXML_001 = f'<definitions xmlns="{BPMN_NS}" id="d" targetNamespace="urn:x"><process>'
FX_BADXML_002 = FX_VALID_001[: len(FX_VALID_001) // 2]

FX_NOTBPMN_001 = '<?xml version="1.0"?><note><to>x</to></note>'
FX_NS_001 = '<?xml version="1.0"?><definitions xmlns="http://example.com/not-bpmn" id="d" targetNamespace="urn:x"/>'
FX_NS_002 = HEADER.replace('targetNamespace="urn:test" ', "") + """
  <bpmn:process id="Process_1" isExecutable="false"/>
""" + FOOTER
FX_NS_003 = '<?xml version="1.0"?><bpmn:definitions xmlns:bpmn="' + BPMN_NS + '" id="d" targetNamespace="urn:x"><undeclared:x/></bpmn:definitions>'

FX_SEC_001 = ('<?xml version="1.0"?><!DOCTYPE definitions [<!ELEMENT definitions ANY>]>'
              + HEADER.split("\n", 1)[1].replace('id="Definitions_1"', 'id="d1"')
              + '<bpmn:process id="p"/>' + FOOTER)
FX_SEC_002 = ('<?xml version="1.0"?><!DOCTYPE definitions [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
              + HEADER.split("\n", 1)[1].replace('id="Definitions_1"', 'id="d2"')
              + '<bpmn:process id="p"/>' + FOOTER)
FX_REC_001 = HEADER + FOOTER
FX_DUP_001 = HEADER + """
  <bpmn:process id="Process_1"><bpmn:task id="Task_1"/><bpmn:task id="Task_1"/></bpmn:process>
""" + FOOTER

FX_REF_001 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:sequenceFlow id="F1" sourceRef="GHOST" targetRef="T1"/></bpmn:process>
""" + FOOTER
FX_REF_002 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:sequenceFlow id="F1" sourceRef="T1" targetRef="GHOST"/></bpmn:process>
""" + FOOTER
FX_REF_003 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:dataObject id="DO1"/>
  <bpmn:sequenceFlow id="F1" sourceRef="T1" targetRef="DO1"/></bpmn:process>
""" + FOOTER
FX_REF_004 = HEADER + """
  <bpmn:collaboration id="C"><bpmn:participant id="P1" processRef="NOPE"/></bpmn:collaboration>
  <bpmn:process id="Real"/>
""" + FOOTER
FX_REF_005 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:boundaryEvent id="B1" attachedToRef="DO1"/><bpmn:dataObject id="DO1"/></bpmn:process>
""" + FOOTER
FX_REF_006 = HEADER + """
  <bpmn:process id="P"><bpmn:laneSet><bpmn:lane id="L1"><bpmn:flowNodeRef>NOPE</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet><bpmn:task id="T1"/></bpmn:process>
""" + FOOTER

FX_REF_007 = HEADER + """
  <bpmn:collaboration id="C"><bpmn:participant id="P1" processRef="P"/>
  <bpmn:messageFlow id="M1" sourceRef="GHOST" targetRef="P1"/></bpmn:collaboration>
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
""" + FOOTER
FX_REF_008 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:association id="A1" sourceRef="GHOST" targetRef="T1"/></bpmn:process>
""" + FOOTER
FX_REF_009 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"><bpmn:dataInputAssociation id="A1" sourceRef="GHOST"/></bpmn:task></bpmn:process>
""" + FOOTER
FX_FLOW_001 = HEADER + """
  <bpmn:collaboration id="C">
    <bpmn:participant id="PA" processRef="ProcessA"/><bpmn:participant id="PB" processRef="ProcessB"/>
  </bpmn:collaboration>
  <bpmn:process id="ProcessA"><bpmn:task id="TA"/></bpmn:process>
  <bpmn:process id="ProcessB"><bpmn:task id="TB"/></bpmn:process>
  <bpmn:collaboration id="C2"><bpmn:sequenceFlow id="FX" sourceRef="TA" targetRef="TB"/></bpmn:collaboration>
""" + FOOTER

# NOTE: cross-pool sequenceFlow must live inside a process for STRUCT checks;
# SEM-001 catches endpoints in different containers even when flow sits in one.
FX_FLOW_001 = HEADER + """
  <bpmn:collaboration id="C">
    <bpmn:participant id="PA" processRef="ProcessA"/><bpmn:participant id="PB" processRef="ProcessB"/>
  </bpmn:collaboration>
  <bpmn:process id="ProcessA"><bpmn:task id="TA"/><bpmn:sequenceFlow id="FX" sourceRef="TA" targetRef="TB"/></bpmn:process>
  <bpmn:process id="ProcessB"><bpmn:task id="TB"/></bpmn:process>
""" + FOOTER

FX_FLOW_002 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="TA"/><bpmn:task id="TB"/>
    <bpmn:messageFlow id="MF" sourceRef="TA" targetRef="TB"/></bpmn:process>
""" + FOOTER

FX_GW_001 = HEADER + """
  <bpmn:process id="P">
    <bpmn:eventBasedGateway id="G1"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:eventBasedGateway>
    <bpmn:task id="T1"/><bpmn:sequenceFlow id="F1" sourceRef="G1" targetRef="T1"/>
  </bpmn:process>
""" + FOOTER

FX_GW_002 = HEADER + """
  <bpmn:process id="P">
    <bpmn:task id="T1" default="F1"/>
    <bpmn:sequenceFlow id="F1" sourceRef="T1" targetRef="T2">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">x</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:task id="T2"/>
  </bpmn:process>
""" + FOOTER

FX_BND_001 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/>
    <bpmn:boundaryEvent id="B1" attachedToRef="T1" cancelActivity="false">
      <bpmn:errorEventDefinition id="ED1"/>
    </bpmn:boundaryEvent></bpmn:process>
""" + FOOTER

FX_LINK_001 = HEADER + """
  <bpmn:process id="P">
    <bpmn:intermediateCatchEvent id="C1"><bpmn:linkEventDefinition id="LD1" name="hop"/></bpmn:intermediateCatchEvent>
  </bpmn:process>
""" + FOOTER

FX_FLOW_003 = HEADER + """
  <bpmn:collaboration id="C">
    <bpmn:participant id="PB"/>
    <bpmn:messageFlow id="MF" sourceRef="PB" targetRef="TA"/>
  </bpmn:collaboration>
  <bpmn:process id="OrphanProcess"><bpmn:task id="TA"/></bpmn:process>
""" + FOOTER

FX_FLOW_004 = HEADER + """
  <bpmn:process id="P"><bpmn:sequenceFlow id="F1"/></bpmn:process>
""" + FOOTER

FX_DI_001 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="P">
    <bpmndi:BPMNShape id="SX" bpmnElement="GHOST"><dc:Bounds x="1" y="1" width="10" height="10"/></bpmndi:BPMNShape>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
""" + FOOTER

FX_DI_002 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="P">
    <bpmndi:BPMNEdge id="EX" bpmnElement="GHOST"><di:waypoint x="1" y="1"/><di:waypoint x="2" y="2"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
""" + FOOTER

FX_DI_003 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/><bpmn:sequenceFlow id="F1" sourceRef="T1" targetRef="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="P">
    <bpmndi:BPMNEdge id="E1" bpmnElement="F1"><di:waypoint x="1" y="1"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
""" + FOOTER

FX_DI_004 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P"/></bpmndi:BPMNDiagram>
  <bpmndi:BPMNDiagram id="D2"><bpmndi:BPMNPlane id="PL2" bpmnElement="P"/></bpmndi:BPMNDiagram>
""" + FOOTER

FX_DI_005 = FX_NODI_002

FX_DI_006 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="GHOST"/></bpmndi:BPMNDiagram>
""" + FOOTER

FX_DI_007 = HEADER + """
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="P">
    <bpmndi:BPMNShape id="S1" bpmnElement="T1"><dc:Bounds x="0" y="0" width="0" height="0"/>
      <bpmndi:BPMNLabel/></bpmndi:BPMNShape>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
""" + FOOTER

FX_PROD_001 = HEADER + """
  <bpmn:process id="P"><bpmn:subProcess id="SP1"/><bpmn:task id="T1"/></bpmn:process>
""" + FOOTER

FX_PROD_002 = HEADER + """
  <bpmn:collaboration id="C"><bpmn:participant id="PB"/></bpmn:collaboration>
  <bpmn:process id="P"><bpmn:task id="T1"/></bpmn:process>
  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="C">
    <bpmndi:BPMNShape id="PS" bpmnElement="PB" isExpanded="true"><dc:Bounds x="1" y="1" width="10" height="10"/></bpmndi:BPMNShape>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
""" + FOOTER

FX_EXT_001 = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:vend="http://vendor.example/x" '
    'id="d" targetNamespace="urn:x">\n'
    '<bpmn:process id="P"><bpmn:task id="T1">'
    '<bpmn:extensionElements><vend:prop key="a"/></bpmn:extensionElements>'
    "</bpmn:task></bpmn:process>" + FOOTER
)

FX_EXT_002 = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:vend="http://vendor.example/x" '
    'id="d" targetNamespace="urn:x">\n'
    '<bpmn:process id="P"><bpmn:task id="T1" vend:custom="yes"/></bpmn:process>' + FOOTER
)

FX_EXT_003 = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:vend="http://vendor.example/x" '
    'id="d" targetNamespace="urn:x">\n'
    '<bpmn:extension definition="vend:prop" mustUnderstand="true"/>\n'
    '<bpmn:process id="P"><bpmn:task id="T1">'
    '<bpmn:extensionElements><vend:prop key="a"/></bpmn:extensionElements>'
    "</bpmn:task></bpmn:process>" + FOOTER
)

FX_EXT_004 = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:vend="http://vendor.example/x" '
    'id="d" targetNamespace="urn:x">\n'
    '<bpmn:extension definition="vend:prop" mustUnderstand="false"/>\n'
    '<bpmn:process id="P"><bpmn:task id="T1">'
    '<bpmn:extensionElements><vend:prop key="a"/></bpmn:extensionElements>'
    "</bpmn:task></bpmn:process>" + FOOTER
)

FX_PRESERVE_001 = HEADER + """
  <bpmn:process id="P">
    <bpmn:complexGateway id="CG1"/>
    <bpmn:adHocSubProcess id="AH1"><bpmn:task id="T1"/></bpmn:adHocSubProcess>
    <bpmn:transaction id="TR1"><bpmn:task id="T2"/></bpmn:transaction>
    <bpmn:eventSubProcess id="ES1"><bpmn:startEvent id="S1"/></bpmn:eventSubProcess>
    <bpmn:dataObject id="DO1"/>
  </bpmn:process>
""" + FOOTER
