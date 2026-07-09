import { estimateNodeSize } from "./diagramConnectionHandles";

export const EDGE_PATH_OFFSET_STEP = 20;
export const EDGE_LABEL_NODE_PADDING = 10;
export const EDGE_LABEL_NUDGE_STEP = 14;
export const EDGE_LABEL_MAX_NUDGES = 8;

type RoutableEdge = {
  id: string;
  source: string;
  target: string;
};

type RoutableNode = {
  id: string;
  position: { x: number; y: number };
  width?: number;
  height?: number;
  type?: string;
};

export type EdgeLabelAnchor = { x: number; y: number };

function spreadOffset(edgeId: string, peerIds: string[], step: number): number {
  const sorted = [...new Set(peerIds)].sort();
  const center = (sorted.length - 1) / 2;
  const index = sorted.indexOf(edgeId);
  if (index < 0) return 0;
  return (index - center) * step;
}

/** Distribui curvas paralelas quando várias conexões saem ou entram no mesmo nó. */
export function computeEdgePathOffsets(edges: ReadonlyArray<RoutableEdge>): Map<string, number> {
  const offsets = new Map<string, number>();
  const bySource = new Map<string, string[]>();
  const byTarget = new Map<string, string[]>();

  for (const edge of edges) {
    const sourceBucket = bySource.get(edge.source) ?? [];
    sourceBucket.push(edge.id);
    bySource.set(edge.source, sourceBucket);

    const targetBucket = byTarget.get(edge.target) ?? [];
    targetBucket.push(edge.id);
    byTarget.set(edge.target, targetBucket);
  }

  for (const edge of edges) {
    const outgoing = bySource.get(edge.source) ?? [];
    const incoming = byTarget.get(edge.target) ?? [];

    if (outgoing.length > 1) {
      offsets.set(edge.id, spreadOffset(edge.id, outgoing, EDGE_PATH_OFFSET_STEP));
      continue;
    }
    if (incoming.length > 1) {
      offsets.set(edge.id, spreadOffset(edge.id, incoming, EDGE_PATH_OFFSET_STEP));
    }
  }

  return offsets;
}

function nodeRect(node: RoutableNode) {
  const size = estimateNodeSize(node.type);
  return {
    x: node.position.x,
    y: node.position.y,
    width: node.width ?? size.width,
    height: node.height ?? size.height,
  };
}

function pointInsideNode(px: number, py: number, node: RoutableNode, padding: number): boolean {
  const rect = nodeRect(node);
  return (
    px >= rect.x - padding &&
    px <= rect.x + rect.width + padding &&
    py >= rect.y - padding &&
    py <= rect.y + rect.height + padding
  );
}

function labelObstructed(
  x: number,
  y: number,
  nodes: RoutableNode[],
  sourceNodeId: string,
  targetNodeId: string,
  padding: number
): boolean {
  for (const node of nodes) {
    if (node.id === sourceNodeId || node.id === targetNodeId) continue;
    if (pointInsideNode(x, y, node, padding)) return true;
  }
  return false;
}

/** Desloca rótulo da aresta para não ficar sobre nós intermediários. */
export function adjustEdgeLabelPosition(
  anchor: EdgeLabelAnchor,
  context: {
    sourceX: number;
    sourceY: number;
    targetX: number;
    targetY: number;
    sourceNodeId: string;
    targetNodeId: string;
  },
  nodes: RoutableNode[]
): EdgeLabelAnchor {
  let { x, y } = anchor;
  if (
    !labelObstructed(
      x,
      y,
      nodes,
      context.sourceNodeId,
      context.targetNodeId,
      EDGE_LABEL_NODE_PADDING
    )
  ) {
    return { x, y };
  }

  const dx = context.targetX - context.sourceX;
  const dy = context.targetY - context.sourceY;
  const length = Math.hypot(dx, dy) || 1;
  const ux = dx / length;
  const uy = dy / length;
  const perpX = -uy;
  const perpY = ux;

  for (let step = 1; step <= EDGE_LABEL_MAX_NUDGES; step += 1) {
    const delta = EDGE_LABEL_NUDGE_STEP * step;
    const candidates: EdgeLabelAnchor[] = [
      { x: x + perpX * delta, y: y + perpY * delta },
      { x: x - perpX * delta, y: y - perpY * delta },
      { x: x + ux * delta, y: y + uy * delta },
      { x: x - ux * delta, y: y - uy * delta },
    ];

    for (const candidate of candidates) {
      if (
        !labelObstructed(
          candidate.x,
          candidate.y,
          nodes,
          context.sourceNodeId,
          context.targetNodeId,
          EDGE_LABEL_NODE_PADDING
        )
      ) {
        return candidate;
      }
    }
  }

  return { x, y };
}
