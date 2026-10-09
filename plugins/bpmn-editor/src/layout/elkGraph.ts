/**
 * Layout graph construction — modelo de cálculo EFÊMERO (P5 §5 NO SECOND MODEL).
 * O ELK graph nunca é persistido nem enviado ao backend.
 *
 * Input: elementos extraídos do moddle tree (via adapter — o grafo é
 * construído dentro de src/layout/ a partir de um snapshot serializável).
 * Ordenação estável: document order com tie-break por id (P5 §39).
 *
 * Hierarquia: node.parentId é derivado da semântica BPMN no snapshot
 * (participant.processRef / lane.flowNodeRef / subProcess.flowElements)
 * — o ELK recebe o containment real, não um flat layout.
 */

import {
  LAYOUT_PROFILE_V1,
  elkPaddingFor,
  nodeSizeFor,
} from "./layoutProfile";

export type LayoutNode = {
  id: string;
  type: string;
  parentId?: string;
  isBoundary?: boolean;
  attachedToId?: string;
  isLane?: boolean;
  isParticipant?: boolean;
  /** BPMNShape.isExpanded vigente (subProcess expandido=true / collapsed=false). */
  isExpanded?: boolean;
  /** Texto do elemento (attr name semântico) — insumo do text-fit G9. */
  label?: string;
  /** Bounds DI atuais — auto-layout preserva o tamanho de não-containers. */
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  /** BPMNLabel explícito do DI (label externa). */
  labelBounds?: LayoutBounds;
  /** Atributos BPMNShape originais além de id/bpmnElement (isExpanded,
   *  isHorizontal, isMarkerVisible, bioc:* etc.) — preservados no preview. */
  diAttrs?: Record<string, string>;
  /** id original da BPMNShape — reutilizado no preview DI. */
  diId?: string;
  /** IDs de elementos geometricamente contidos neste bpmn:group antes do
   *  layout (artifact visual, SEM ownership semântico). Derivado do
   *  BPMN-DI corrente no snapshot; usado só para re-bounds pós-ELK. */
  visualMembers?: string[];
};

export type LayoutEdge = {
  id: string;
  sourceId: string;
  targetId: string;
  /** Waypoints DI atuais — necessários para mover a label da edge. */
  points?: { x: number; y: number }[];
  /** BPMNLabel explícito do DI. */
  labelBounds?: LayoutBounds;
  /** Atributos BPMNEdge originais além de id/bpmnElement. */
  diAttrs?: Record<string, string>;
  /** id original da BPMNEdge — reutilizado no preview DI. */
  diId?: string;
};

export type LayoutBounds = { x: number; y: number; width: number; height: number };

export type LayoutSnapshot = {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
};

export type ElkNode = {
  id: string;
  /** x/y preenchidos pelo ELK no output (input não precisa). */
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  children?: ElkNode[];
  edges?: ElkEdge[];
  layoutOptions?: Record<string, string>;
};

export type ElkEdge = {
  id: string;
  sources: string[];
  targets: string[];
};

const COLLAPSED = (n: LayoutNode) => n.isExpanded === false;

/** Padding interno do container ELK conforme a família BPMN — lane/pool
 *  reservam o header vertical à esquerda (`containerPadFor`, fonte única
 *  compartilhada com o container-fit pós-ELK em diProposal). */
function containerPadding(node: LayoutNode): string {
  const type = node.type.replace(/^bpmn:/, "");
  if (node.isParticipant) return elkPaddingFor("participant");
  if (node.isLane) return elkPaddingFor("lane");
  if (
    type === "subProcess" ||
    type === "transaction" ||
    type === "adHocSubProcess" ||
    type === "eventSubProcess"
  ) {
    return elkPaddingFor("subprocess");
  }
  return elkPaddingFor("default");
}

/** Constrói o grafo ELK hierárquico a partir do snapshot. Determinístico.
 *  Descendentes de containers collapsed não entram no grafo (conteúdo
 *  não visível não é laid out). Edges cujo scope real é um ancestor
 *  comum (cross-lane, cross-pool) são declaradas no LCA — exigência do
 *  ELK layered para hyperedges hierárquicas. */
export function buildElkGraph(snapshot: LayoutSnapshot): ElkNode {
  const nodeById = new Map(snapshot.nodes.map((n) => [n.id, n]));
  const parentOf = new Map(snapshot.nodes.map((n) => [n.id, n.parentId]));

  // Nós escondidos: descendem (transitivo) de um container collapsed.
  const hidden = new Set<string>();
  for (const node of snapshot.nodes) {
    let p = parentOf.get(node.id);
    while (p) {
      const parent = nodeById.get(p);
      if (!parent) break;
      if (COLLAPSED(parent) || hidden.has(p)) {
        hidden.add(node.id);
        break;
      }
      p = parentOf.get(p);
    }
  }
  // Visível = existe e não está dentro de um container collapsed.
  const isVisible = (id: string) => nodeById.has(id) && !hidden.has(id);
  const isGroup = (id: string) => nodeById.get(id)?.type === "bpmn:group";
  // bpmn:group é artifact VISUAL — não entra no grafo ELK (não é
  // container semântico). Seus bounds são recalculados pós-layout a
  // partir dos visualMembers derivados do DI (diProposal).
  const sortedNodes = [...snapshot.nodes]
    .filter((n) => !hidden.has(n.id) && n.type !== "bpmn:group")
    .sort((a, b) => a.id.localeCompare(b.id));
  const sortedEdges = [...snapshot.edges].sort((a, b) =>
    a.id.localeCompare(b.id),
  );

  const byParent = new Map<string | undefined, LayoutNode[]>();
  for (const node of sortedNodes) {
    const list = byParent.get(node.parentId) ?? [];
    list.push(node);
    byParent.set(node.parentId, list);
  }

  /** Cadeia de ancestors (exclusivo) até a raiz. */
  const ancestors = (id: string): Array<string | undefined> => {
    const chain: Array<string | undefined> = [];
    let p = parentOf.get(id);
    while (p !== undefined) {
      chain.push(p);
      p = parentOf.get(p);
    }
    chain.push(undefined);
    return chain;
  };

  /** Menor ancestor comum dos dois endpoints — scope válido da edge. */
  const edgeScope = (
    edge: LayoutEdge,
  ): string | undefined => {
    const a = ancestors(edge.sourceId);
    const b = new Set(ancestors(edge.targetId));
    return a.find((anc) => b.has(anc));
  };

  const edgesByScope = new Map<string | undefined, LayoutEdge[]>();
  for (const edge of sortedEdges) {
    // Endpoints precisam existir e estar visíveis no grafo.
    if (!isVisible(edge.sourceId) || !isVisible(edge.targetId)) continue;
    // Edges ligadas a bpmn:group (association) ficam fora do ELK — o
    // endpoint não é node do grafo. Seus waypoints DI são preservados.
    if (isGroup(edge.sourceId) || isGroup(edge.targetId)) continue;
    const scope = edgeScope(edge);
    const list = edgesByScope.get(scope) ?? [];
    list.push(edge);
    edgesByScope.set(scope, list);
  }

  const build = (parentId: string | undefined): ElkNode[] =>
    (byParent.get(parentId) ?? []).map((node) => {
      const size =
        node.width != null && node.height != null
          ? { width: node.width, height: node.height }
          : nodeSizeFor(node.type);
      const children = COLLAPSED(node) ? [] : build(node.id);
      const elkNode: ElkNode = {
        id: node.id,
        width: size.width,
        height: size.height,
      };
      if (children.length > 0) {
        elkNode.children = children;
        // Lane stacking/order é política de composição BPMN — aplicada
        // na normalização pós-ELK (diProposal), não via ELK options
        // (considerModelOrder + hierarquia crasha elkjs 0.12).
        elkNode.layoutOptions = {
          ...LAYOUT_PROFILE_V1.elk,
          "elk.padding": containerPadding(node),
        };
        const scoped = edgesByScope.get(node.id);
        if (scoped?.length) {
          elkNode.edges = scoped.map(toElkEdge);
        }
      }
      return elkNode;
    });

  const rootChildren = build(undefined);
  const rootEdges = (edgesByScope.get(undefined) ?? []).map(toElkEdge);

  return {
    id: "__root__",
    layoutOptions: { ...LAYOUT_PROFILE_V1.elk },
    children: rootChildren,
    edges: rootEdges,
  };
}

function toElkEdge(edge: LayoutEdge): ElkEdge {
  return { id: edge.id, sources: [edge.sourceId], targets: [edge.targetId] };
}
