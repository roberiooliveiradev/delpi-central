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
  /** Macro ∩ escopo — base absoluta para gravar o overlay. */
  flowchart_base?: FlowchartV1;
  flowchart_reference?: FlowchartV1 | null;
  mermaid: string;
  warnings: string[];
  escopo: FlowchartEscopo;
  overlay: FlowchartOverlayV1;
  seeded_from_reference?: boolean;
  referencia?: {
    revisao_id: string;
    versao_revisao?: string;
    cenario_tipo?: string;
  } | null;
  baseline_diff?: DiagramDiff | null;
  reference_diff?: DiagramDiff | null;
};

export type ComposedProcessoDiagram = {
  processo_id: string;
  at: string;
  instancia_id?: string | null;
  flowchart: FlowchartV1;
  mermaid: string;
  applied_revisoes: Array<{
    revisao_id: string;
    instancia_id: string;
    versao_revisao?: string;
    cenario_tipo?: string;
    data_inicio_vigencia?: string;
    node_ids_tocados: string[];
  }>;
  conflicts: Array<{
    node_id: string;
    field: string;
    winner_revisao_id: string;
    revisoes: Array<{
      revisao_id: string;
      versao_revisao?: string;
      label?: string | null;
    }>;
  }>;
  base_node_count?: number;
};
