import {
  BPMN_NODE_DEFINITIONS,
  FLOWCHART_NODE_PALETTE,
  FLOWCHART_NODE_TYPES,
  isEndEventType,
  isGatewayType,
  isKnownFlowchartNodeType,
  isManualTaskType,
  isNonFlowNodeType,
  isStartEventType,
  normalizeFlowchartNodeType,
  paletteByCategory,
  emptyFlowchart,
  emptyOverlay,
  emptyEscopo,
  createNodeId,
  createEdgeId,
  createLaneId,
  applySwimlaneBpmnTemplate,
  applyLinearTemplate,
  applyDecisionTemplate,
  flowToOverlayDraft,
  overlayToEditableFlowchart,
  type FlowchartNodeType,
  type FlowchartLane,
  type FlowchartNode,
  type FlowchartEdgeRouting,
  type FlowchartEdgeKind,
  type FlowchartEdge,
  type FlowchartV1,
  type FlowchartEscopo,
  type FlowchartOverlayV1,
} from "@delpi/plugin-ui/index";

export type {
  FlowchartNodeType,
  FlowchartLane,
  FlowchartNode,
  FlowchartEdgeRouting,
  FlowchartEdgeKind,
  FlowchartEdge,
  FlowchartV1,
  FlowchartEscopo,
  FlowchartOverlayV1,
};

export {
  BPMN_NODE_DEFINITIONS,
  FLOWCHART_NODE_PALETTE,
  FLOWCHART_NODE_TYPES,
  isEndEventType,
  isGatewayType,
  isKnownFlowchartNodeType,
  isManualTaskType,
  isNonFlowNodeType,
  isStartEventType,
  normalizeFlowchartNodeType,
  paletteByCategory,
  emptyFlowchart,
  emptyOverlay,
  emptyEscopo,
  createNodeId,
  createEdgeId,
  createLaneId,
  applySwimlaneBpmnTemplate,
  applyLinearTemplate,
  applyDecisionTemplate,
  flowToOverlayDraft,
  overlayToEditableFlowchart,
};

export type ProcessoDiagramResponse = {
  processo_id: string | null;
  conteudo: FlowchartV1;
  mermaid: string;
  empty?: boolean;
  updated_at?: string;
};

export type DiagramDiff = {
  changed: string[];
  added: string[];
  removed: string[];
};

export type MergedRevisaoDiagram = {
  revisao_id: string;
  cenario_tipo?: string;
  flowchart: FlowchartV1;
  mermaid: string;
  warnings: string[];
  escopo: FlowchartEscopo;
  overlay: FlowchartOverlayV1;
  baseline_diff?: DiagramDiff | null;
};
