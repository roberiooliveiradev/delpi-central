export type FlowchartNodeType =
  | "start"
  | "end"
  | "process"
  | "decision"
  | "document"
  | "data"
  | "subprocess"
  | "comment";

export type FlowchartLane = {
  id: string;
  label: string;
  height?: number;
  order?: number;
};

export type FlowchartNode = {
  id: string;
  type: FlowchartNodeType;
  label: string;
  position: { x: number; y: number };
  lane_id?: string;
  disabled?: boolean;
  highlight?: "asis" | "tobe" | "changed" | "removed";
  meta?: {
    manual?: boolean;
    [key: string]: unknown;
  };
};

export type FlowchartEdgeRouting = "straight" | "step" | "smoothstep";

export type FlowchartEdge = {
  id: string;
  from: string;
  to: string;
  label?: string | null;
  routing?: FlowchartEdgeRouting;
};

export type FlowchartV1 = {
  format: "flowchart_v1";
  format_version: 1;
  lanes?: FlowchartLane[];
  nodes: FlowchartNode[];
  edges: FlowchartEdge[];
};

export type FlowchartEscopo = {
  node_ids: string[];
  inherit_all: boolean;
  include_boundary_edges?: boolean;
};

export type FlowchartOverlayV1 = {
  format: "flowchart_overlay_v1";
  format_version: 1;
  modo?: "full_scope" | "partial";
  node_overrides?: Record<
    string,
    {
      label?: string;
      type?: FlowchartNodeType;
      position?: { x: number; y: number };
      lane_id?: string;
      highlight?: "asis" | "tobe" | "changed" | "removed";
      meta?: FlowchartNode["meta"];
    }
  >;
  edge_overrides?: Record<
    string,
    { label?: string | null; from?: string; to?: string; routing?: FlowchartEdgeRouting }
  >;
  removed_node_ids?: string[];
  removed_edge_ids?: string[];
  extra_nodes?: FlowchartNode[];
  extra_edges?: FlowchartEdge[];
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

export function emptyFlowchart(): FlowchartV1 {
  return {
    format: "flowchart_v1",
    format_version: 1,
    nodes: [],
    edges: [],
  };
}

export function emptyOverlay(): FlowchartOverlayV1 {
  return {
    format: "flowchart_overlay_v1",
    format_version: 1,
    modo: "full_scope",
    node_overrides: {},
    edge_overrides: {},
    removed_node_ids: [],
    removed_edge_ids: [],
    extra_nodes: [],
    extra_edges: [],
  };
}

export function emptyEscopo(): FlowchartEscopo {
  return {
    node_ids: [],
    inherit_all: true,
    include_boundary_edges: false,
  };
}

export function createNodeId(prefix = "n"): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

export function createEdgeId(): string {
  return `e_${Math.random().toString(36).slice(2, 9)}`;
}

export const FLOWCHART_NODE_PALETTE: Array<{ type: FlowchartNodeType; label: string }> = [
  { type: "start", label: "Início" },
  { type: "process", label: "Atividade" },
  { type: "decision", label: "Decisão" },
  { type: "document", label: "Documento" },
  { type: "data", label: "Dado" },
  { type: "subprocess", label: "Subprocesso" },
  { type: "end", label: "Fim" },
  { type: "comment", label: "Nota" },
];

export function createLaneId(): string {
  return `lane_${Math.random().toString(36).slice(2, 9)}`;
}

export function applySwimlaneBpmnTemplate(): FlowchartV1 {
  const laneComercial = createLaneId();
  const laneEngenharia = createLaneId();

  const start = createNodeId("start");
  const crm = createNodeId("proc");
  const handoff = createNodeId("proc");
  const validar = createNodeId("proc");
  const gatewayInfo = createNodeId("dec");
  const solicitar = createNodeId("proc");
  const elaborar = createNodeId("proc");
  const gatewayRev = createNodeId("dec");
  const end = createNodeId("end");

  const lanes: FlowchartLane[] = [
    { id: laneComercial, label: "Comercial", height: 168, order: 0 },
    {
      id: laneEngenharia,
      label: "LMP — Lançamento e Modificação de Produtos / Engenharia",
      height: 168,
      order: 1,
    },
  ];

  return {
    format: "flowchart_v1",
    format_version: 1,
    lanes,
    nodes: [
      {
        id: start,
        type: "start",
        label: "Recebimento de nova demanda no CRM",
        lane_id: laneComercial,
        position: { x: 168, y: 56 },
      },
      {
        id: crm,
        type: "process",
        label: "Registrar oportunidade e anexos no CRM",
        lane_id: laneComercial,
        position: { x: 420, y: 48 },
        meta: { manual: true },
      },
      {
        id: handoff,
        type: "process",
        label: "Encaminhar demanda para Engenharia",
        lane_id: laneComercial,
        position: { x: 700, y: 48 },
        meta: { manual: true },
      },
      {
        id: validar,
        type: "process",
        label: "Validar informações técnicas recebidas",
        lane_id: laneEngenharia,
        position: { x: 168, y: 224 },
        meta: { manual: true },
      },
      {
        id: gatewayInfo,
        type: "decision",
        label: "Informações completas?",
        lane_id: laneEngenharia,
        position: { x: 460, y: 216 },
      },
      {
        id: solicitar,
        type: "process",
        label: "Solicitar informações faltantes ao cliente",
        lane_id: laneComercial,
        position: { x: 980, y: 48 },
        meta: { manual: true },
      },
      {
        id: elaborar,
        type: "process",
        label: "Elaborar lançamento / modificação de produto",
        lane_id: laneEngenharia,
        position: { x: 700, y: 224 },
        meta: { manual: true },
      },
      {
        id: gatewayRev,
        type: "decision",
        label: "Revisão técnica aprovada?",
        lane_id: laneEngenharia,
        position: { x: 980, y: 216 },
      },
      {
        id: end,
        type: "end",
        label: "Fim",
        lane_id: laneEngenharia,
        position: { x: 1240, y: 224 },
      },
    ],
    edges: [
      { id: createEdgeId(), from: start, to: crm, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: crm, to: handoff, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: handoff, to: validar, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: validar, to: gatewayInfo, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: gatewayInfo, to: elaborar, label: "Sim", routing: "smoothstep" },
      { id: createEdgeId(), from: gatewayInfo, to: solicitar, label: "Não", routing: "smoothstep" },
      { id: createEdgeId(), from: solicitar, to: validar, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: elaborar, to: gatewayRev, label: null, routing: "smoothstep" },
      { id: createEdgeId(), from: gatewayRev, to: end, label: "Sim", routing: "smoothstep" },
      { id: createEdgeId(), from: gatewayRev, to: elaborar, label: "Não", routing: "smoothstep" },
    ],
  };
}

export function applyLinearTemplate(): FlowchartV1 {
  const n1 = createNodeId("start");
  const n2 = createNodeId("proc");
  const n3 = createNodeId("end");
  return {
    format: "flowchart_v1",
    format_version: 1,
    nodes: [
      { id: n1, type: "start", label: "Início", position: { x: 40, y: 120 } },
      { id: n2, type: "process", label: "Atividade", position: { x: 220, y: 120 } },
      { id: n3, type: "end", label: "Fim", position: { x: 420, y: 120 } },
    ],
    edges: [
      { id: createEdgeId(), from: n1, to: n2, label: null },
      { id: createEdgeId(), from: n2, to: n3, label: null },
    ],
  };
}

export function applyDecisionTemplate(): FlowchartV1 {
  const start = createNodeId("start");
  const proc = createNodeId("proc");
  const decision = createNodeId("dec");
  const yes = createNodeId("yes");
  const no = createNodeId("no");
  const end = createNodeId("end");
  return {
    format: "flowchart_v1",
    format_version: 1,
    nodes: [
      { id: start, type: "start", label: "Início", position: { x: 40, y: 160 } },
      { id: proc, type: "process", label: "Entrada", position: { x: 180, y: 160 } },
      { id: decision, type: "decision", label: "Condição?", position: { x: 340, y: 160 } },
      { id: yes, type: "process", label: "Sim", position: { x: 520, y: 80 } },
      { id: no, type: "process", label: "Não", position: { x: 520, y: 240 } },
      { id: end, type: "end", label: "Fim", position: { x: 700, y: 160 } },
    ],
    edges: [
      { id: createEdgeId(), from: start, to: proc, label: null },
      { id: createEdgeId(), from: proc, to: decision, label: null },
      { id: createEdgeId(), from: decision, to: yes, label: "Sim" },
      { id: createEdgeId(), from: decision, to: no, label: "Não" },
      { id: createEdgeId(), from: yes, to: end, label: null },
      { id: createEdgeId(), from: no, to: end, label: null },
    ],
  };
}

export function flowToOverlayDraft(
  base: FlowchartV1,
  edited: FlowchartV1,
  previous: FlowchartOverlayV1 = emptyOverlay()
): FlowchartOverlayV1 {
  const baseById = new Map(base.nodes.map((node) => [node.id, node]));
  const nodeOverrides = { ...(previous.node_overrides ?? {}) };

  for (const node of edited.nodes) {
    const original = baseById.get(node.id);
    if (!original) continue;
    const changed =
      original.label !== node.label ||
      original.type !== node.type ||
      original.position.x !== node.position.x ||
      original.position.y !== node.position.y ||
      original.lane_id !== node.lane_id ||
      node.highlight;
    if (changed) {
      nodeOverrides[node.id] = {
        ...(nodeOverrides[node.id] ?? {}),
        label: node.label,
        type: node.type,
        position: node.position,
        lane_id: node.lane_id,
        highlight: node.highlight,
        meta: node.meta,
      };
    }
  }

  return {
    ...emptyOverlay(),
    ...previous,
    node_overrides: nodeOverrides,
  };
}

export function overlayToEditableFlowchart(merged: FlowchartV1): FlowchartV1 {
  return merged;
}
