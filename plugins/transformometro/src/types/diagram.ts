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
} from "@delpi/plugin-ui";

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
} from "@delpi/plugin-ui";

export type ProcessoDiagramResponse = {
  processo_id: string | null;
  conteudo: import("@delpi/plugin-ui").FlowchartV1;
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
  flowchart: import("@delpi/plugin-ui").FlowchartV1;
  mermaid: string;
  warnings: string[];
  escopo: import("@delpi/plugin-ui").FlowchartEscopo;
  overlay: import("@delpi/plugin-ui").FlowchartOverlayV1;
  baseline_diff?: DiagramDiff | null;
};
