import {
  createEdgeId,
  createNodeId,
  emptyFlowchart,
  type FlowchartNode,
  type FlowchartNodeType,
  type FlowchartV1,
} from "../types/diagram";

const NODE_TYPES = new Set<FlowchartNodeType>([
  "start",
  "end",
  "process",
  "decision",
  "document",
  "data",
  "subprocess",
  "comment",
]);

function sanitizeMermaidId(nodeId: string): string {
  const cleaned = nodeId.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!cleaned) return "node";
  if (/^\d/.test(cleaned)) return `n_${cleaned}`;
  return cleaned;
}

function escapeLabel(label: string): string {
  return label.replace(/"/g, "'").replace(/\n/g, " ").trim();
}

function nodeShape(nodeType: FlowchartNodeType, mermaidId: string, label: string): string {
  const text = escapeLabel(label);
  if (nodeType === "decision") return `    ${mermaidId}{"${text}"}`;
  if (nodeType === "start" || nodeType === "end") return `    ${mermaidId}(("${text}"))`;
  if (nodeType === "comment") return `    ${mermaidId}[/"${text}"/]`;
  return `    ${mermaidId}["${text}"]`;
}

export function flowchartToMermaid(flowchart: FlowchartV1): string {
  const nodes = flowchart.nodes ?? [];
  const edges = flowchart.edges ?? [];

  if (!nodes.length) {
    return 'flowchart TD\n    empty["Diagrama vazio"]';
  }

  const lines = ["flowchart TD"];
  const idMap = new Map<string, string>();

  for (const node of nodes) {
    const rawId = String(node.id ?? "");
    if (!rawId) continue;
    let nodeType = node.type;
    if (!NODE_TYPES.has(nodeType)) nodeType = "process";
    const mermaidId = sanitizeMermaidId(rawId);
    idMap.set(rawId, mermaidId);
    let line = nodeShape(nodeType, mermaidId, String(node.label || rawId));
    const highlight = node.highlight ?? node.meta?.highlight;
    if (highlight === "asis" || highlight === "tobe" || highlight === "changed" || highlight === "removed") {
      line = `${line}:::highlight_${highlight}`;
    }
    lines.push(line);
  }

  for (const edge of edges) {
    const fromId = String(edge.from ?? "");
    const toId = String(edge.to ?? "");
    if (!idMap.has(fromId) || !idMap.has(toId)) continue;
    const from = idMap.get(fromId)!;
    const to = idMap.get(toId)!;
    if (edge.label) {
      lines.push(`    ${from} -->|"${escapeLabel(String(edge.label))}"| ${to}`);
    } else {
      lines.push(`    ${from} --> ${to}`);
    }
  }

  const highlights = new Set(
    nodes
      .map((node) => node.highlight ?? node.meta?.highlight)
      .filter((value): value is NonNullable<FlowchartNode["highlight"]> => Boolean(value))
  );
  if (highlights.size) {
    if (highlights.has("asis")) {
      lines.push("    classDef highlight_asis fill:#fef3c7,stroke:#d97706");
    }
    if (highlights.has("tobe")) {
      lines.push("    classDef highlight_tobe fill:#dbeafe,stroke:#2563eb");
    }
    if (highlights.has("changed")) {
      lines.push("    classDef highlight_changed fill:#fce7f3,stroke:#db2777");
    }
    if (highlights.has("removed")) {
      lines.push("    classDef highlight_removed fill:#f3f4f6,stroke:#9ca3af,stroke-dasharray:4");
    }
  }

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
  shape: "box" | "stadium" | "decision" | "comment";
  highlight?: FlowchartNode["highlight"];
};

function parseNodeLine(line: string): ParsedNode | null {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("classDef") || trimmed.startsWith("style ")) return null;

  const classMatch = trimmed.match(/:::(highlight_\w+)$/);
  const highlightToken = classMatch?.[1]?.replace("highlight_", "") as FlowchartNode["highlight"] | undefined;
  const body = classMatch ? trimmed.replace(/\s*:::highlight_\w+$/, "") : trimmed;

  const stadium = body.match(/^(\w+)\(\("([^"]*)"\)\)$/);
  if (stadium) {
    return { id: stadium[1], label: stadium[2], shape: "stadium", highlight: highlightToken };
  }

  const decision = body.match(/^(\w+)\{"([^"]*)"\}$/);
  if (decision) {
    return { id: decision[1], label: decision[2], shape: "decision", highlight: highlightToken };
  }

  const comment = body.match(/^(\w+)\[\/"([^"]*)"\/\]$/);
  if (comment) {
    return { id: comment[1], label: comment[2], shape: "comment", highlight: highlightToken };
  }

  const box = body.match(/^(\w+)\["([^"]*)"\]$/);
  if (box) {
    if (box[1] === "empty" && /diagrama vazio/i.test(box[2])) return null;
    return { id: box[1], label: box[2], shape: "box", highlight: highlightToken };
  }

  return null;
}

function parseEdgeLine(line: string): { from: string; to: string; label?: string } | null {
  const trimmed = line.trim();
  const match = trimmed.match(/^(\w+)\s*-->\s*(?:\|"([^"]*)"\|\s*)?(\w+)\s*$/);
  if (!match) return null;
  return {
    from: match[1],
    to: match[3],
    label: match[2]?.trim() || undefined,
  };
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
  const parsedEdges: Array<{ from: string; to: string; label?: string }> = [];

  for (const line of lines.slice(1)) {
    const edge = parseEdgeLine(line);
    if (edge) {
      parsedEdges.push(edge);
      continue;
    }
    const node = parseNodeLine(line);
    if (node) parsedNodes.push(node);
  }

  if (!parsedNodes.length && !parsedEdges.length) {
    return emptyFlowchart();
  }

  if (!parsedNodes.length) {
    throw new MermaidImportError("Nenhum nó reconhecido no código Mermaid.");
  }

  const stadiumNodes = parsedNodes.filter((node) => node.shape === "stadium");

  const nodes: FlowchartNode[] = parsedNodes.map((node, index) => {
    let type: FlowchartNodeType = "process";
    if (node.shape === "decision") type = "decision";
    else if (node.shape === "comment") type = "comment";
    else if (node.shape === "stadium") {
      type = inferStadiumType(node.label, stadiumNodes.indexOf(node), stadiumNodes.length);
    }

    return {
      id: node.id,
      type,
      label: node.label || node.id,
      position: { x: 80 + index * 180, y: 120 },
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
    }));

  return {
    ...base,
    format: "flowchart_v1",
    format_version: 1,
    lanes: undefined,
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
    `    ${sanitizeMermaidId(start)}(("Início"))`,
    `    ${sanitizeMermaidId(proc)}["Atividade"]`,
    `    ${sanitizeMermaidId(end)}(("Fim"))`,
    `    ${sanitizeMermaidId(start)} --> ${sanitizeMermaidId(proc)}`,
    `    ${sanitizeMermaidId(proc)} --> ${sanitizeMermaidId(end)}`,
  ].join("\n");
}
