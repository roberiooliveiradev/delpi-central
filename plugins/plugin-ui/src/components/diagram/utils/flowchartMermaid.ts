import {
  createEdgeId,
  createNodeId,
  emptyFlowchart,
  normalizeFlowchartNodeType,
  type FlowchartEdgeKind,
  type FlowchartLane,
  type FlowchartNode,
  type FlowchartNodeType,
  type FlowchartV1,
} from "../types/diagram";
import {
  bpmnMermaidClassForType,
  buildBpmnCatalogForApi,
  formatMermaidNodeLine,
  inferNodeTypeFromMermaidShape,
  mermaidClassDefLines,
  mermaidEdgeSyntax,
  mermaidHighlightClassDefLines,
  parseMermaidNodeTypeFromClass,
  wrapMermaidLabelText,
} from "./bpmnMermaidMapping";
import { MERMAID_LANE_LABEL_WRAPPING_WIDTH } from "./mermaidPreviewConfig";

export { buildBpmnCatalogForApi };

function sanitizeMermaidId(nodeId: string): string {
  const cleaned = nodeId.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!cleaned) return "node";
  if (/^\d/.test(cleaned)) return `n_${cleaned}`;
  return cleaned;
}

function escapeLabel(label: string): string {
  return label.replace(/"/g, "'").replace(/\n/g, " ").trim();
}

function normalizeImportedMermaidLabel(label: string): string {
  return label
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function laneSubgraphId(laneId: string): string {
  return sanitizeMermaidId(`lane_${laneId}`);
}

function formatLaneSubgraphLabel(label: string): string {
  return wrapMermaidLabelText(escapeLabel(label), MERMAID_LANE_LABEL_WRAPPING_WIDTH);
}

export function flowchartToMermaid(flowchart: FlowchartV1): string {
  const nodes = flowchart.nodes ?? [];
  const edges = flowchart.edges ?? [];
  const lanes = flowchart.lanes ?? [];

  if (!nodes.length) {
    return 'flowchart TD\n    empty["Diagrama vazio"]';
  }

  const lines = ["flowchart TD"];
  const idMap = new Map<string, string>();
  const usedClasses = new Set<string>();

  const writeNode = (node: FlowchartNode, indent: string) => {
    const rawId = String(node.id ?? "");
    if (!rawId) return;
    const nodeType = normalizeFlowchartNodeType(String(node.type ?? "process"));
    const mermaidId = sanitizeMermaidId(rawId);
    idMap.set(rawId, mermaidId);
    let line = formatMermaidNodeLine(nodeType, mermaidId, String(node.label || rawId));
    usedClasses.add(bpmnMermaidClassForType(nodeType));
    const highlight = node.highlight ?? node.meta?.highlight;
    if (highlight === "asis" || highlight === "tobe" || highlight === "changed" || highlight === "removed") {
      line = `${line} highlight_${highlight}`;
    }
    lines.push(`${indent}${line}`);
  };

  if (lanes.length) {
    const laneById = new Map(lanes.map((lane) => [lane.id, lane]));
    const nodesByLane = new Map<string, FlowchartNode[]>();
    const unassigned: FlowchartNode[] = [];

    for (const node of nodes) {
      if (node.lane_id && laneById.has(node.lane_id)) {
        const bucket = nodesByLane.get(node.lane_id) ?? [];
        bucket.push(node);
        nodesByLane.set(node.lane_id, bucket);
      } else {
        unassigned.push(node);
      }
    }

    for (const lane of lanes) {
      const laneNodes = nodesByLane.get(lane.id) ?? [];
      if (!laneNodes.length) continue;
      lines.push(
        `    subgraph ${laneSubgraphId(lane.id)} ["${formatLaneSubgraphLabel(lane.label)}"]`
      );
      for (const node of laneNodes) {
        writeNode(node, "        ");
      }
      lines.push("    end");
    }

    for (const node of unassigned) {
      writeNode(node, "    ");
    }
  } else {
    for (const node of nodes) {
      writeNode(node, "    ");
    }
  }

  for (const edge of edges) {
    const fromId = String(edge.from ?? "");
    const toId = String(edge.to ?? "");
    if (!idMap.has(fromId) || !idMap.has(toId)) continue;
    const from = idMap.get(fromId)!;
    const to = idMap.get(toId)!;
    const kind = (edge.kind ?? "sequence") as FlowchartEdgeKind;
    lines.push(mermaidEdgeSyntax(from, to, kind, edge.label));
  }

  lines.push(...mermaidClassDefLines(usedClasses));

  const highlights = new Set(
    nodes
      .map((node) => node.highlight ?? node.meta?.highlight)
      .filter((value): value is NonNullable<FlowchartNode["highlight"]> => Boolean(value))
  );
  lines.push(...mermaidHighlightClassDefLines(highlights));

  return lines.join("\n");
}

export class MermaidImportError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MermaidImportError";
  }
}

function inferStadiumType(label: string, index: number, total: number): FlowchartNodeType {
  const normalized = label.trim().toLowerCase();
  if (/^(in[ií]cio|start|inicio)$/.test(normalized)) return "start";
  if (/^(fim|end|t[eé]rmino|termino)$/.test(normalized)) return "end";
  if (index === 0) return "start";
  if (index === total - 1 && total > 1) return "end";
  return "process";
}

type ParsedNode = {
  id: string;
  label: string;
  shape: "box" | "stadium" | "decision" | "comment" | "subroutine" | "parallelogram" | "cylinder" | "circle";
  classType?: FlowchartNodeType;
  highlight?: FlowchartNode["highlight"];
  laneId?: string;
};

function parseClassTokens(raw: string): { body: string; classes: string[] } {
  const classes = [...raw.matchAll(/:::(\w+)/g)].map((match) => match[1]);
  const body = raw.replace(/\s*:::\w+/g, "").trim();
  return { body, classes };
}

function parseNodeLine(line: string, laneId?: string): ParsedNode | null {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("classDef") || trimmed.startsWith("style ")) return null;

  const { body, classes } = parseClassTokens(trimmed);
  const highlightToken = classes.find((token) => token.startsWith("highlight_"))?.replace("highlight_", "") as
    | FlowchartNode["highlight"]
    | undefined;
  const classType = classes
    .map((token) => parseMermaidNodeTypeFromClass(token))
    .find((value): value is FlowchartNodeType => Boolean(value));

  const stadium = body.match(/^(\w+)\(\("([^"]*)"\)\)$/);
  if (stadium) {
    return {
      id: stadium[1],
      label: stadium[2],
      shape: classType && classType.startsWith("intermediate") ? "circle" : "stadium",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const cylinder = body.match(/^(\w+)\[\("([^"]*)"\)\]$/);
  if (cylinder) {
    return {
      id: cylinder[1],
      label: cylinder[2],
      shape: "cylinder",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const decision = body.match(/^(\w+)\{"([^"]*)"\}$/);
  if (decision) {
    return {
      id: decision[1],
      label: decision[2],
      shape: "decision",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const subroutine = body.match(/^(\w+)\[\["([^"]*)"\]\]$/);
  if (subroutine) {
    return {
      id: subroutine[1],
      label: subroutine[2],
      shape: "subroutine",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const parallelogram = body.match(/^(\w+)\[\/"([^"]*)"\/\]$/);
  if (parallelogram) {
    return {
      id: parallelogram[1],
      label: parallelogram[2],
      shape: "parallelogram",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const comment = body.match(/^(\w+)\[\/"([^"]*)"\/\]$/);
  if (comment) {
    return {
      id: comment[1],
      label: comment[2],
      shape: "comment",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  const box = body.match(/^(\w+)\["([^"]*)"\]$/);
  if (box) {
    if (box[1] === "empty" && /diagrama vazio/i.test(box[2])) return null;
    return {
      id: box[1],
      label: box[2],
      shape: "box",
      classType,
      highlight: highlightToken,
      laneId,
    };
  }

  return null;
}

function parseEdgeLine(
  line: string
): { from: string; to: string; label?: string; kind: FlowchartEdgeKind } | null {
  const trimmed = line.trim();
  const association = trimmed.match(/^(\w+)\s*-\.-\s*(?:\|"([^"]*)"\|\s*)?(\w+)\s*$/);
  if (association) {
    return {
      from: association[1],
      to: association[3],
      label: association[2]?.trim() || undefined,
      kind: "association",
    };
  }

  const message = trimmed.match(/^(\w+)\s*-\.->\s*(?:\|"([^"]*)"\|\s*)?(\w+)\s*$/);
  if (message) {
    return {
      from: message[1],
      to: message[3],
      label: message[2]?.trim() || undefined,
      kind: "message_flow",
    };
  }

  const sequence = trimmed.match(/^(\w+)\s*-->\s*(?:\|"([^"]*)"\|\s*)?(\w+)\s*$/);
  if (sequence) {
    return {
      from: sequence[1],
      to: sequence[3],
      label: sequence[2]?.trim() || undefined,
      kind: "sequence",
    };
  }

  return null;
}

function parseSubgraphHeader(line: string): { laneId: string; label: string } | null {
  const trimmed = line.trim();
  const match = trimmed.match(/^subgraph\s+(\w+)\s+\["([^"]*)"\]\s*$/i);
  if (!match) return null;
  const laneId = match[1].startsWith("lane_") ? match[1].slice(5) : match[1];
  return { laneId, label: match[2] };
}

export function mermaidToFlowchart(code: string, base: FlowchartV1 = emptyFlowchart()): FlowchartV1 {
  const lines = String(code || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    throw new MermaidImportError("Informe um diagrama Mermaid válido.");
  }

  const header = lines[0];
  if (!/^flowchart\s+(TD|LR|BT|RL)$/i.test(header)) {
    throw new MermaidImportError('A primeira linha deve ser "flowchart TD" (ou LR/BT/RL).');
  }

  const parsedNodes: ParsedNode[] = [];
  const parsedEdges: Array<{ from: string; to: string; label?: string; kind: FlowchartEdgeKind }> = [];
  const parsedLanes: FlowchartLane[] = [];
  let currentLaneId: string | undefined;
  let laneOrder = 0;

  for (const line of lines.slice(1)) {
    if (/^end$/i.test(line)) {
      currentLaneId = undefined;
      continue;
    }

    const subgraph = parseSubgraphHeader(line);
    if (subgraph) {
      currentLaneId = subgraph.laneId;
      parsedLanes.push({
        id: subgraph.laneId,
        label: subgraph.label,
        order: laneOrder,
        height: 168,
      });
      laneOrder += 1;
      continue;
    }

    const edge = parseEdgeLine(line);
    if (edge) {
      parsedEdges.push(edge);
      continue;
    }

    const node = parseNodeLine(line, currentLaneId);
    if (node) parsedNodes.push(node);
  }

  if (!parsedNodes.length && !parsedEdges.length) {
    return emptyFlowchart();
  }

  if (!parsedNodes.length) {
    throw new MermaidImportError("Nenhum nó reconhecido no código Mermaid.");
  }

  const stadiumNodes = parsedNodes.filter((node) => node.shape === "stadium" || node.shape === "circle");

  const nodes: FlowchartNode[] = parsedNodes.map((node, index) => {
    let type = inferNodeTypeFromMermaidShape(node.shape, node.classType);
    if (!node.classType && (node.shape === "stadium" || node.shape === "circle")) {
      type = inferStadiumType(node.label, stadiumNodes.indexOf(node), stadiumNodes.length);
    }

    return {
      id: node.id,
      type,
      label: normalizeImportedMermaidLabel(node.label || node.id),
      position: { x: 80 + index * 180, y: 120 + (parsedLanes.findIndex((lane) => lane.id === node.laneId) * 168) },
      lane_id: node.laneId,
      highlight: node.highlight,
    };
  });

  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = parsedEdges
    .filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to))
    .map((edge) => ({
      id: createEdgeId(),
      from: edge.from,
      to: edge.to,
      label: edge.label ?? null,
      kind: edge.kind,
    }));

  return {
    ...base,
    format: "flowchart_v1",
    format_version: 1,
    lanes: parsedLanes.length ? parsedLanes : undefined,
    nodes,
    edges,
  };
}

export function createStarterMermaidTemplate(): string {
  const start = createNodeId("start");
  const proc = createNodeId("proc");
  const end = createNodeId("end");
  return [
    "flowchart TD",
    `    ${formatMermaidNodeLine("start", sanitizeMermaidId(start), "Início")}`,
    `    ${formatMermaidNodeLine("process", sanitizeMermaidId(proc), "Atividade")}`,
    `    ${formatMermaidNodeLine("end", sanitizeMermaidId(end), "Fim")}`,
    `    ${sanitizeMermaidId(start)} --> ${sanitizeMermaidId(proc)}`,
    `    ${sanitizeMermaidId(proc)} --> ${sanitizeMermaidId(end)}`,
    ...mermaidClassDefLines(["bpmn_start", "bpmn_process", "bpmn_end"]),
  ].join("\n");
}
