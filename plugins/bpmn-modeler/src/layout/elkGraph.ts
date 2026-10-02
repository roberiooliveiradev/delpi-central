/**
 * Layout graph construction — modelo de cálculo EFÊMERO (P5 §5 NO SECOND MODEL).
 * O ELK graph nunca é persistido nem enviado ao backend.
 *
 * Input: elementos extraídos do moddle tree (via adapter — o grafo é
 * construído dentro de src/layout/ a partir de um snapshot serializável).
 * Ordenação estável: document order com tie-break por id (P5 §39).
 */

import { LAYOUT_PROFILE_V1, nodeSizeFor } from "./layoutProfile";

export type LayoutNode = {
  id: string;
  type: string;
  parentId?: string;
  isBoundary?: boolean;
  attachedToId?: string;
  isLane?: boolean;
  isParticipant?: boolean;
  /** Bounds DI atuais — auto-layout preserva o tamanho de não-containers. */
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  /** BPMNLabel explícito do DI (label externa). */
  labelBounds?: LayoutBounds;
};

export type LayoutEdge = {
  id: string;
  sourceId: string;
  targetId: string;
  /** Waypoints DI atuais — necessários para mover a label da edge. */
  points?: { x: number; y: number }[];
  /** BPMNLabel explícito do DI. */
  labelBounds?: LayoutBounds;
};

export type LayoutBounds = { x: number; y: number; width: number; height: number };

export type LayoutSnapshot = {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
};

export type ElkNode = {
  id: string;
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

/** Constrói o grafo ELK hierárquico a partir do snapshot. Determinístico. */
export function buildElkGraph(snapshot: LayoutSnapshot): ElkNode {
  const sortedNodes = [...snapshot.nodes].sort((a, b) =>
    a.id.localeCompare(b.id),
  );
  const sortedEdges = [...snapshot.edges].sort((a, b) =>
    a.id.localeCompare(b.id),
  );

  const byParent = new Map<string | undefined, LayoutNode[]>();
  for (const node of sortedNodes) {
    const list = byParent.get(node.parentId) ?? [];
    list.push(node);
    byParent.set(node.parentId, list);
  }

  const edgesByScope = new Map<string | undefined, LayoutEdge[]>();
  const nodeById = new Map(sortedNodes.map((n) => [n.id, n]));
  for (const edge of sortedEdges) {
    const source = nodeById.get(edge.sourceId);
    const scope = source?.parentId;
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
      const children = build(node.id);
      const elkNode: ElkNode = {
        id: node.id,
        width: size.width,
        height: size.height,
      };
      if (children.length > 0) {
        elkNode.children = children;
        elkNode.layoutOptions = { ...LAYOUT_PROFILE_V1.elk };
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
