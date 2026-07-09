import {
  BPMN_NODE_DEFINITIONS,
  FLOWCHART_NODE_TYPES,
  isKnownFlowchartNodeType,
  normalizeFlowchartNodeType,
  type BpmnShapeFamily,
  type FlowchartNodeType,
} from "../types/bpmnNodeCatalog";

export const BPMN_MERMAID_CLASS_PREFIX = "bpmn_";

export type BpmnMermaidShapeKind =
  | "stadium"
  | "circle"
  | "rhombus"
  | "rectangle"
  | "subroutine"
  | "parallelogram"
  | "cylinder"
  | "comment";

export type BpmnMermaidClassDef = {
  fill: string;
  stroke: string;
  color?: string;
  strokeWidth?: string;
  strokeDasharray?: string;
};

const SHAPE_KIND_BY_FAMILY: Record<BpmnShapeFamily, BpmnMermaidShapeKind> = {
  event_start: "stadium",
  event_end: "stadium",
  event_intermediate_catch: "circle",
  event_intermediate_throw: "circle",
  gateway: "rhombus",
  task: "rectangle",
  activity_subprocess: "rectangle",
  activity_call: "subroutine",
  activity_ad_hoc: "rectangle",
  activity_transaction: "rectangle",
  activity_event_subprocess: "rectangle",
  artifact_document: "subroutine",
  artifact_data_store: "cylinder",
  artifact_data_object: "parallelogram",
  artifact_comment: "comment",
  artifact_group: "rectangle",
  boundary: "circle",
};

export type MermaidPaletteTheme = "light" | "dark";

const CLASS_DEFS_LIGHT: Record<string, BpmnMermaidClassDef> = {
  bpmn_event_start: { fill: "#ecfdf5", stroke: "#16a34a", color: "#15803d" },
  bpmn_event_end: { fill: "#fff", stroke: "#dc2626", color: "#b91c1c", strokeWidth: "3px" },
  bpmn_event_intermediate: { fill: "#fff", stroke: "#64748b", color: "#475569", strokeWidth: "2px" },
  bpmn_event_intermediate_throw: { fill: "#f8fafc", stroke: "#ea580c", color: "#c2410c" },
  bpmn_gateway_exclusive: { fill: "#fbbf24", stroke: "#d97706", color: "#78350f" },
  bpmn_gateway_parallel: { fill: "#7dd3fc", stroke: "#0284c7", color: "#0c4a6e" },
  bpmn_gateway_inclusive: { fill: "#c4b5fd", stroke: "#7c3aed", color: "#4c1d95" },
  bpmn_gateway_complex: { fill: "#fde68a", stroke: "#ca8a04", color: "#713f12" },
  bpmn_gateway_event: { fill: "#fbcfe8", stroke: "#db2777", color: "#831843" },
  bpmn_task: { fill: "#ecfdf5", stroke: "#059669", color: "#047857" },
  bpmn_activity_subprocess: { fill: "#ede9fe", stroke: "#7c3aed", color: "#6d28d9" },
  bpmn_activity_call: { fill: "#ede9fe", stroke: "#7c3aed", color: "#6d28d9", strokeWidth: "4px" },
  bpmn_activity_ad_hoc: { fill: "#f5f3ff", stroke: "#9333ea", color: "#7e22ce", strokeDasharray: "4 3" },
  bpmn_activity_transaction: { fill: "#d1fae5", stroke: "#059669", color: "#047857", strokeWidth: "4px" },
  bpmn_activity_event_subprocess: { fill: "#ffedd5", stroke: "#ea580c", color: "#c2410c", strokeDasharray: "6 4" },
  bpmn_artifact_document: { fill: "#fef3c7", stroke: "#d97706", color: "#b45309" },
  bpmn_artifact_data_object: { fill: "#f8fafc", stroke: "#64748b", color: "#334155" },
  bpmn_artifact_data_store: { fill: "#dbeafe", stroke: "#2563eb", color: "#1d4ed8" },
  bpmn_artifact_comment: { fill: "#f0f9ff", stroke: "#089bdb", color: "#0c4a6e", strokeDasharray: "5 3" },
  bpmn_artifact_group: { fill: "#f8fafc", stroke: "#94a3b8", color: "#475569", strokeDasharray: "8 4" },
  bpmn_boundary: { fill: "#fff7ed", stroke: "#ea580c", color: "#c2410c", strokeWidth: "3px" },
};

const CLASS_DEFS_DARK: Record<string, BpmnMermaidClassDef> = {
  bpmn_event_start: { fill: "#14532d", stroke: "#22c55e", color: "#bbf7d0" },
  bpmn_event_end: { fill: "#1f1416", stroke: "#f87171", color: "#fecaca", strokeWidth: "3px" },
  bpmn_event_intermediate: { fill: "#1e293b", stroke: "#94a3b8", color: "#e2e8f0", strokeWidth: "2px" },
  bpmn_event_intermediate_throw: { fill: "#431407", stroke: "#fb923c", color: "#fed7aa" },
  bpmn_gateway_exclusive: { fill: "#78350f", stroke: "#fbbf24", color: "#fef3c7" },
  bpmn_gateway_parallel: { fill: "#0c4a6e", stroke: "#38bdf8", color: "#e0f2fe" },
  bpmn_gateway_inclusive: { fill: "#4c1d95", stroke: "#a78bfa", color: "#ede9fe" },
  bpmn_gateway_complex: { fill: "#713f12", stroke: "#facc15", color: "#fef9c3" },
  bpmn_gateway_event: { fill: "#831843", stroke: "#f472b6", color: "#fce7f3" },
  bpmn_task: { fill: "#1e293b", stroke: "#34d399", color: "#d1fae5" },
  bpmn_activity_subprocess: { fill: "#312e81", stroke: "#a78bfa", color: "#ede9fe" },
  bpmn_activity_call: { fill: "#312e81", stroke: "#a78bfa", color: "#ede9fe", strokeWidth: "4px" },
  bpmn_activity_ad_hoc: { fill: "#3b0764", stroke: "#c084fc", color: "#f3e8ff", strokeDasharray: "4 3" },
  bpmn_activity_transaction: { fill: "#064e3b", stroke: "#34d399", color: "#d1fae5", strokeWidth: "4px" },
  bpmn_activity_event_subprocess: { fill: "#431407", stroke: "#fb923c", color: "#ffedd5", strokeDasharray: "6 4" },
  bpmn_artifact_document: { fill: "#78350f", stroke: "#fbbf24", color: "#fef3c7" },
  bpmn_artifact_data_object: { fill: "#1e293b", stroke: "#94a3b8", color: "#e2e8f0" },
  bpmn_artifact_data_store: { fill: "#1e3a5f", stroke: "#60a5fa", color: "#dbeafe" },
  bpmn_artifact_comment: { fill: "#0c4a6e", stroke: "#38bdf8", color: "#e0f2fe", strokeDasharray: "5 3" },
  bpmn_artifact_group: { fill: "#1e293b", stroke: "#64748b", color: "#cbd5e1", strokeDasharray: "8 4" },
  bpmn_boundary: { fill: "#431407", stroke: "#fb923c", color: "#ffedd5", strokeWidth: "3px" },
};

const HIGHLIGHT_DEFS_LIGHT: Record<string, BpmnMermaidClassDef> = {
  asis: { fill: "#fef3c7", stroke: "#d97706", color: "#92400e" },
  tobe: { fill: "#dbeafe", stroke: "#2563eb", color: "#1e40af" },
  changed: { fill: "#fce7f3", stroke: "#db2777", color: "#9d174d" },
  removed: { fill: "#f3f4f6", stroke: "#9ca3af", color: "#6b7280", strokeDasharray: "4" },
};

const HIGHLIGHT_DEFS_DARK: Record<string, BpmnMermaidClassDef> = {
  asis: { fill: "#78350f", stroke: "#fbbf24", color: "#fef3c7" },
  tobe: { fill: "#1e3a8a", stroke: "#60a5fa", color: "#dbeafe" },
  changed: { fill: "#831843", stroke: "#f472b6", color: "#fce7f3" },
  removed: { fill: "#1f2937", stroke: "#6b7280", color: "#9ca3af", strokeDasharray: "4" },
};

function classDefsForTheme(theme: MermaidPaletteTheme): Record<string, BpmnMermaidClassDef> {
  return theme === "dark" ? CLASS_DEFS_DARK : CLASS_DEFS_LIGHT;
}

function formatClassDefLine(group: string, style: BpmnMermaidClassDef): string {
  const parts = [`fill:${style.fill}`, `stroke:${style.stroke}`];
  if (style.color) parts.push(`color:${style.color}`);
  if (style.strokeWidth) parts.push(`stroke-width:${style.strokeWidth}`);
  if (style.strokeDasharray) parts.push(`stroke-dasharray:${style.strokeDasharray}`);
  return `    classDef ${group} ${parts.join(",")}`;
}

function mermaidVisualGroup(nodeType: FlowchartNodeType): string {
  const def = BPMN_NODE_DEFINITIONS[nodeType];
  if (def.shape === "gateway") {
    if (nodeType === "gateway_parallel") return "bpmn_gateway_parallel";
    if (nodeType === "gateway_inclusive") return "bpmn_gateway_inclusive";
    if (nodeType === "gateway_complex") return "bpmn_gateway_complex";
    if (nodeType === "gateway_event") return "bpmn_gateway_event";
    return "bpmn_gateway_exclusive";
  }
  if (def.shape === "event_start") return "bpmn_event_start";
  if (def.shape === "event_end") return "bpmn_event_end";
  if (def.shape === "event_intermediate_throw") return "bpmn_event_intermediate_throw";
  if (def.shape === "event_intermediate_catch") return "bpmn_event_intermediate";
  if (def.shape === "boundary") return "bpmn_boundary";
  if (def.shape === "activity_call") return "bpmn_activity_call";
  if (def.shape === "activity_ad_hoc") return "bpmn_activity_ad_hoc";
  if (def.shape === "activity_transaction") return "bpmn_activity_transaction";
  if (def.shape === "activity_event_subprocess") return "bpmn_activity_event_subprocess";
  if (def.shape === "activity_subprocess") return "bpmn_activity_subprocess";
  if (def.shape === "artifact_document") return "bpmn_artifact_document";
  if (def.shape === "artifact_data_object") return "bpmn_artifact_data_object";
  if (def.shape === "artifact_data_store") return "bpmn_artifact_data_store";
  if (def.shape === "artifact_comment") return "bpmn_artifact_comment";
  if (def.shape === "artifact_group") return "bpmn_artifact_group";
  return "bpmn_task";
}

export function bpmnMermaidClassForType(nodeType: FlowchartNodeType): string {
  return `${BPMN_MERMAID_CLASS_PREFIX}${normalizeFlowchartNodeType(nodeType)}`;
}

export function bpmnMermaidShapeKindForType(nodeType: FlowchartNodeType): BpmnMermaidShapeKind {
  const def = BPMN_NODE_DEFINITIONS[normalizeFlowchartNodeType(nodeType)];
  return SHAPE_KIND_BY_FAMILY[def.shape];
}

const MERMAID_WRAP_MAX_BY_SHAPE: Record<BpmnMermaidShapeKind, number> = {
  stadium: 16,
  circle: 16,
  rhombus: 18,
  rectangle: 24,
  subroutine: 22,
  parallelogram: 22,
  cylinder: 22,
  comment: 22,
};

/** Quebra rótulos longos com `<br>` para preview Mermaid (htmlLabels). */
export function wrapMermaidLabelText(label: string, maxLineLength: number): string {
  const normalized = label.replace(/"/g, "'").replace(/\n/g, " ").replace(/\s+/g, " ").trim();
  if (!normalized || normalized.length <= maxLineLength) {
    return normalized;
  }

  const lines: string[] = [];
  let current = "";

  for (const word of normalized.split(" ")) {
    if (!current) {
      current = word;
      continue;
    }
    const candidate = `${current} ${word}`;
    if (candidate.length <= maxLineLength) {
      current = candidate;
      continue;
    }
    lines.push(current);
    current = word;
  }

  if (current) {
    lines.push(current);
  }

  return lines.join("<br>");
}

export function formatMermaidNodeLine(
  nodeType: FlowchartNodeType,
  mermaidId: string,
  label: string
): string {
  const kind = bpmnMermaidShapeKindForType(nodeType);
  const text = wrapMermaidLabelText(label, MERMAID_WRAP_MAX_BY_SHAPE[kind]);
  let body = "";
  switch (kind) {
    case "stadium":
      body = `${mermaidId}(("${text}"))`;
      break;
    case "circle":
      body = `${mermaidId}(("${text}"))`;
      break;
    case "rhombus":
      body = `${mermaidId}{"${text}"}`;
      break;
    case "subroutine":
      body = `${mermaidId}[["${text}"]]`;
      break;
    case "parallelogram":
      body = `${mermaidId}[/"${text}"/]`;
      break;
    case "cylinder":
      body = `${mermaidId}[("${text}")]`;
      break;
    case "comment":
      body = `${mermaidId}[/"${text}"/]`;
      break;
    default:
      body = `${mermaidId}["${text}"]`;
      break;
  }
  return `${body}:::${bpmnMermaidClassForType(nodeType)}`;
}

export function mermaidClassDefLines(
  usedClasses: Iterable<string>,
  theme: MermaidPaletteTheme = "light"
): string[] {
  const palette = classDefsForTheme(theme);
  const groups = new Set<string>();
  for (const className of usedClasses) {
    if (!className.startsWith(BPMN_MERMAID_CLASS_PREFIX)) continue;
    const nodeType = className.slice(BPMN_MERMAID_CLASS_PREFIX.length);
    if (!isKnownFlowchartNodeType(nodeType)) continue;
    groups.add(mermaidVisualGroup(nodeType));
  }

  return [...groups]
    .map((group) => {
      const style = palette[group];
      return style ? formatClassDefLine(group, style) : "";
    })
    .filter(Boolean);
}

export function mermaidHighlightClassDefLines(
  highlights: Iterable<string>,
  theme: MermaidPaletteTheme = "light"
): string[] {
  const palette = theme === "dark" ? HIGHLIGHT_DEFS_DARK : HIGHLIGHT_DEFS_LIGHT;
  return [...highlights]
    .map((token) => {
      const style = palette[token];
      return style ? formatClassDefLine(`highlight_${token}`, style) : "";
    })
    .filter(Boolean);
}

export function parseMermaidNodeTypeFromClass(className: string | undefined): FlowchartNodeType | undefined {
  if (!className?.startsWith(BPMN_MERMAID_CLASS_PREFIX)) return undefined;
  const nodeType = className.slice(BPMN_MERMAID_CLASS_PREFIX.length);
  return isKnownFlowchartNodeType(nodeType) ? nodeType : undefined;
}

export function inferNodeTypeFromMermaidShape(
  shape: "box" | "stadium" | "decision" | "comment" | "subroutine" | "parallelogram" | "cylinder" | "circle",
  classType?: FlowchartNodeType
): FlowchartNodeType {
  if (classType) return classType;
  if (shape === "decision") return "decision";
  if (shape === "comment" || shape === "parallelogram") return "comment";
  if (shape === "cylinder") return "data";
  if (shape === "subroutine") return "subprocess";
  if (shape === "stadium" || shape === "circle") return "process";
  return "process";
}

export function mermaidEdgeSyntax(
  from: string,
  to: string,
  kind: "sequence" | "message_flow" | "association" = "sequence",
  label?: string | null
): string {
  const escaped = label?.replace(/"/g, "'").replace(/\n/g, " ").trim();
  if (kind === "message_flow") {
    return escaped
      ? `    ${from} -.->|"${escaped}"| ${to}`
      : `    ${from} -.-> ${to}`;
  }
  if (kind === "association") {
    return escaped
      ? `    ${from} -.-|"${escaped}"| ${to}`
      : `    ${from} -.- ${to}`;
  }
  return escaped ? `    ${from} -->|"${escaped}"| ${to}` : `    ${from} --> ${to}`;
}

export function buildBpmnCatalogForApi() {
  return {
    format: "transformometro_bpmn_catalog_v1" as const,
    format_version: 1 as const,
    node_types: FLOWCHART_NODE_TYPES.map((type) => {
      const def = BPMN_NODE_DEFINITIONS[type];
      const sampleId = "exemplo";
      const sampleLabel = def.label;
      return {
        id: type,
        label: def.label,
        category: def.category,
        shape: def.shape,
        marker: def.marker,
        bpmn_tag: def.bpmnTag,
        bpmn_event_definition: "bpmnEventDefinition" in def ? def.bpmnEventDefinition ?? null : null,
        participates_in_flow: def.participatesInFlow,
        hint: def.hint,
        mermaid: {
          class: bpmnMermaidClassForType(type),
          visual_group: mermaidVisualGroup(type),
          shape_kind: bpmnMermaidShapeKindForType(type),
          example: `    ${formatMermaidNodeLine(type, sampleId, sampleLabel)}`,
        },
      };
    }),
    edge_kinds: [
      {
        id: "sequence",
        label: "Fluxo de sequência",
        mermaid: "A --> B",
        mermaid_labeled: 'A -->|"rótulo"| B',
      },
      {
        id: "message_flow",
        label: "Fluxo de mensagem",
        mermaid: "A -.-> B",
        mermaid_labeled: 'A -.->|"mensagem"| B',
      },
      {
        id: "association",
        label: "Associação",
        mermaid: "A -.- B",
        mermaid_labeled: 'A -.-|"nota"| B',
      },
    ],
    mermaid_conventions: {
      header: "flowchart TD",
      swimlane_syntax: 'subgraph lane_id ["Nome da faixa"] ... end',
      type_class_suffix: ":::bpmn_{node_type}",
      round_trip: "Use sempre a classe :::bpmn_<tipo> em cada nó para round-trip fiel com o canvas.",
      source_of_truth: "flowchart_v1 (JSON) é a fonte de verdade; Mermaid é vista/exportação derivada.",
    },
    ai_guidance: {
      summary:
        "Para gerar diagramas compatíveis com o Transformômetro, use flowchart TD, subgraphs para faixas, classes :::bpmn_<tipo> em todos os nós e arestas --> / -.-> / -.- conforme o tipo de conexão.",
      minimal_example: [
        "flowchart TD",
        '    subgraph lane_vendas ["Vendas"]',
        '        start(("Pedido")):::bpmn_start',
        '        crm["Registrar CRM"]:::bpmn_process',
        "    end",
        '    gateway{"Aprovado?"}:::bpmn_decision',
        '    start --> crm',
        '    crm --> gateway',
      ].join("\n"),
    },
  };
}
