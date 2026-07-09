import type { FlowchartLane, FlowchartNode, FlowchartV1 } from "../types/diagram";

export const LANE_HEADER_WIDTH = 132;
export const DEFAULT_LANE_HEIGHT = 168;
export const LANE_MIN_HEIGHT = 128;
export const LANE_VERTICAL_PADDING = 28;
export const NODE_ESTIMATED_HEIGHT = 104;
export const LANE_CANVAS_WIDTH = 2400;
export const AUTO_LAYOUT_HORIZONTAL_GAP = 220;
export const AUTO_LAYOUT_VERTICAL_GAP = 32;
export const AUTO_LAYOUT_START_X = LANE_HEADER_WIDTH + 48;
export const PALETTE_NODE_GAP_X = 204;
export const PALETTE_NODE_GAP_Y = 116;
export const PALETTE_GRID_COLUMNS = 4;
export const PALETTE_GRID_ORIGIN = { x: 72, y: 72 } as const;

export type SnapNodeToLaneOptions = {
  /** center = legado (centraliza na faixa); preserve = mantém Y; clamp = mantém Y dentro da faixa */
  snapY?: "center" | "preserve" | "clamp";
};


export function requiredLaneHeight(
  laneNodes: FlowchartNode[],
  laneTop: number,
  minHeight = LANE_MIN_HEIGHT
): number {
  if (!laneNodes.length) {
    return DEFAULT_LANE_HEIGHT;
  }

  let maxBottom = laneTop + minHeight;
  for (const node of laneNodes) {
    maxBottom = Math.max(maxBottom, node.position.y + NODE_ESTIMATED_HEIGHT);
  }

  return Math.max(minHeight, maxBottom - laneTop + LANE_VERTICAL_PADDING);
}

export function fitLaneHeightsToContent(flowchart: FlowchartV1): FlowchartV1 {
  const lanes = normalizeLanes(flowchart.lanes);
  if (!lanes.length) {
    return flowchart;
  }

  const oldTops = lanes.map((_, index) => laneTopOffset(lanes, lanes[index].id));
  const newHeights = lanes.map((lane, index) => {
    const laneNodes = flowchart.nodes.filter((node) => node.lane_id === lane.id);
    return requiredLaneHeight(laneNodes, oldTops[index]);
  });

  const updatedLanes = lanes.map((lane, index) => ({
    ...lane,
    height: newHeights[index],
  }));

  const newTops = updatedLanes.map((_, index) => laneTopOffset(updatedLanes, updatedLanes[index].id));
  const updatedNodes = flowchart.nodes.map((node) => {
    if (!node.lane_id) {
      return node;
    }
    const laneIndex = updatedLanes.findIndex((lane) => lane.id === node.lane_id);
    if (laneIndex < 0) {
      return node;
    }
    const delta = newTops[laneIndex] - oldTops[laneIndex];
    if (delta === 0) {
      return node;
    }
    return {
      ...node,
      position: {
        ...node.position,
        y: node.position.y + delta,
      },
    };
  });

  return {
    ...flowchart,
    lanes: updatedLanes,
    nodes: updatedNodes,
  };
}

export function assignNodesToLanes(flowchart: FlowchartV1): FlowchartV1 {
  const lanes = normalizeLanes(flowchart.lanes);
  if (!lanes.length) {
    return flowchart;
  }
  return {
    ...flowchart,
    lanes,
    nodes: flowchart.nodes.map((node) => ({
      ...node,
      lane_id: resolveNodeLaneId(node, lanes) ?? node.lane_id ?? lanes[0].id,
    })),
  };
}

export function normalizeLanes(lanes: FlowchartLane[] | undefined): FlowchartLane[] {
  if (!lanes?.length) {
    return [];
  }
  return lanes.map((lane, index) => ({
    id: lane.id,
    label: lane.label,
    height: lane.height ?? DEFAULT_LANE_HEIGHT,
    order: lane.order ?? index,
  }));
}

export function laneTopOffset(lanes: FlowchartLane[], laneId: string): number {
  let offset = 0;
  for (const lane of lanes) {
    if (lane.id === laneId) {
      return offset;
    }
    offset += lane.height ?? DEFAULT_LANE_HEIGHT;
  }
  return 0;
}

export function laneCenterY(lanes: FlowchartLane[], laneId: string): number {
  const lane = lanes.find((item) => item.id === laneId);
  const height = lane?.height ?? DEFAULT_LANE_HEIGHT;
  return laneTopOffset(lanes, laneId) + height / 2;
}

export function resolveNodeLaneId(node: FlowchartNode, lanes: FlowchartLane[]): string | undefined {
  if (node.lane_id && lanes.some((lane) => lane.id === node.lane_id)) {
    return node.lane_id;
  }
  if (!lanes.length) {
    return undefined;
  }
  const y = node.position.y;
  let offset = 0;
  for (const lane of lanes) {
    const height = lane.height ?? DEFAULT_LANE_HEIGHT;
    if (y >= offset && y < offset + height) {
      return lane.id;
    }
    offset += height;
  }
  return lanes[0]?.id;
}

export function snapNodeToLane(
  node: FlowchartNode,
  lanes: FlowchartLane[],
  laneId?: string,
  options?: SnapNodeToLaneOptions
): FlowchartNode {
  if (!lanes.length) {
    return node;
  }
  const targetLaneId = laneId ?? resolveNodeLaneId(node, lanes) ?? lanes[0].id;
  const top = laneTopOffset(lanes, targetLaneId);
  const lane = lanes.find((item) => item.id === targetLaneId);
  const height = lane?.height ?? DEFAULT_LANE_HEIGHT;
  const snapY = options?.snapY ?? "center";

  let y = node.position.y;
  if (snapY === "center") {
    y = top + height / 2 - NODE_ESTIMATED_HEIGHT / 2 + 8;
  } else if (snapY === "clamp") {
    const minY = top + LANE_VERTICAL_PADDING;
    const maxY = top + height - NODE_ESTIMATED_HEIGHT - LANE_VERTICAL_PADDING;
    y = Math.max(minY, Math.min(maxY, y));
  }

  return {
    ...node,
    lane_id: targetLaneId,
    position: {
      x: Math.max(LANE_HEADER_WIDTH + 24, node.position.x),
      y,
    },
  };
}

export function defaultNodePosition(
  lanes: FlowchartLane[],
  laneId: string,
  indexInLane = 0
): { x: number; y: number } {
  const top = laneTopOffset(lanes, laneId);
  const col = indexInLane % 3;
  const row = Math.floor(indexInLane / 3);
  return {
    x: AUTO_LAYOUT_START_X + col * PALETTE_NODE_GAP_X,
    y: top + LANE_VERTICAL_PADDING + row * PALETTE_NODE_GAP_Y,
  };
}

export function nextPaletteNodePosition(activityIndex: number): { x: number; y: number } {
  const col = activityIndex % PALETTE_GRID_COLUMNS;
  const row = Math.floor(activityIndex / PALETTE_GRID_COLUMNS);
  return {
    x: PALETTE_GRID_ORIGIN.x + col * PALETTE_NODE_GAP_X,
    y: PALETTE_GRID_ORIGIN.y + row * PALETTE_NODE_GAP_Y,
  };
}

export function canvasHeightForLanes(lanes: FlowchartLane[] | undefined, min = 420): number {
  if (!lanes?.length) {
    return min;
  }
  const total = lanes.reduce((sum, lane) => sum + (lane.height ?? DEFAULT_LANE_HEIGHT), 0);
  return Math.max(min, total + 24);
}

export function withNormalizedLanes(flowchart: FlowchartV1): FlowchartV1 {
  return fitLaneHeightsToContent(assignNodesToLanes(flowchart));
}

export function renameLane(
  flowchart: FlowchartV1,
  laneId: string,
  label: string
): FlowchartV1 {
  const trimmed = label.trim();
  if (!trimmed) {
    return flowchart;
  }
  return {
    ...flowchart,
    lanes: (flowchart.lanes ?? []).map((lane) =>
      lane.id === laneId ? { ...lane, label: trimmed } : lane
    ),
  };
}

export function removeLane(flowchart: FlowchartV1, laneId: string): FlowchartV1 {
  const lanes = normalizeLanes(flowchart.lanes);
  if (!lanes.length) {
    return flowchart;
  }

  const nextLanes = lanes.filter((lane) => lane.id !== laneId).map((lane, index) => ({
    ...lane,
    order: index,
  }));
  const fallbackLaneId = nextLanes[0]?.id;

  const nextNodes = flowchart.nodes.map((node) => {
    const currentLaneId = resolveNodeLaneId(node, lanes);
    if (currentLaneId !== laneId) {
      return node;
    }
    if (!fallbackLaneId) {
      const { lane_id: _laneId, ...rest } = node;
      return rest;
    }
    return snapNodeToLane(
      { ...node, lane_id: fallbackLaneId },
      nextLanes,
      fallbackLaneId,
      { snapY: "preserve" }
    );
  });

  const next = {
    ...flowchart,
    lanes: nextLanes.length ? nextLanes : undefined,
    nodes: nextNodes,
  };
  return nextLanes.length ? fitLaneHeightsToContent(next) : next;
}

export function reorderLanes(
  flowchart: FlowchartV1,
  laneId: string,
  toIndex: number
): FlowchartV1 {
  const lanes = normalizeLanes(flowchart.lanes);
  if (!lanes.length) {
    return flowchart;
  }

  const fromIndex = lanes.findIndex((lane) => lane.id === laneId);
  if (fromIndex < 0) {
    return withNormalizedLanes(flowchart);
  }

  const clampedIndex = Math.max(0, Math.min(lanes.length - 1, toIndex));
  if (fromIndex === clampedIndex) {
    return withNormalizedLanes(flowchart);
  }

  const next = [...lanes];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(clampedIndex, 0, moved);

  return withNormalizedLanes({
    ...flowchart,
    lanes: next.map((lane, index) => ({ ...lane, order: index })),
  });
}

export function laneIndexFromDragY(
  lanes: FlowchartLane[],
  laneId: string,
  dragY: number
): number {
  if (!lanes.length) {
    return 0;
  }

  const lane = lanes.find((item) => item.id === laneId);
  const height = lane?.height ?? DEFAULT_LANE_HEIGHT;
  const centerY = dragY + height / 2;

  let offset = 0;
  for (let index = 0; index < lanes.length; index += 1) {
    const laneHeight = lanes[index].height ?? DEFAULT_LANE_HEIGHT;
    if (centerY < offset + laneHeight) {
      return index;
    }
    offset += laneHeight;
  }

  return lanes.length - 1;
}

function findBackEdgeKeys(nodes: FlowchartNode[], edges: FlowchartV1["edges"]): Set<string> {
  const nodeIds = nodes.map((node) => node.id);
  const adjacency = new Map<string, string[]>();
  for (const nodeId of nodeIds) {
    adjacency.set(nodeId, []);
  }
  for (const edge of edges) {
    if (!adjacency.has(edge.from) || !adjacency.has(edge.to)) continue;
    adjacency.get(edge.from)!.push(edge.to);
  }

  const visited = new Set<string>();
  const active = new Set<string>();
  const backEdges = new Set<string>();

  const visit = (nodeId: string) => {
    visited.add(nodeId);
    active.add(nodeId);
    for (const targetId of adjacency.get(nodeId) ?? []) {
      if (!visited.has(targetId)) {
        visit(targetId);
      } else if (active.has(targetId)) {
        backEdges.add(`${nodeId}->${targetId}`);
      }
    }
    active.delete(nodeId);
  };

  for (const nodeId of nodeIds) {
    if (!visited.has(nodeId)) {
      visit(nodeId);
    }
  }

  return backEdges;
}

function longestPathRanks(
  nodes: FlowchartNode[],
  edges: FlowchartV1["edges"]
): Map<string, number> {
  const ranks = new Map<string, number>();
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();

  for (const node of nodes) {
    incoming.set(node.id, []);
    outgoing.set(node.id, []);
  }

  for (const edge of edges) {
    if (!incoming.has(edge.to) || !outgoing.has(edge.from)) {
      continue;
    }
    incoming.get(edge.to)!.push(edge.from);
    outgoing.get(edge.from)!.push(edge.to);
  }

  const seeds = nodes.filter((node) => (incoming.get(node.id)?.length ?? 0) === 0);
  const queue = (seeds.length ? seeds : nodes.filter((node) => node.type === "start")).map(
    (node) => node.id
  );

  if (!queue.length) {
    for (const node of nodes) {
      queue.push(node.id);
    }
  }

  for (const seedId of queue) {
    ranks.set(seedId, 0);
  }

  let guard = 0;
  while (queue.length && guard < nodes.length * nodes.length) {
    guard += 1;
    const nodeId = queue.shift()!;
    const rank = ranks.get(nodeId) ?? 0;
    for (const targetId of outgoing.get(nodeId) ?? []) {
      const nextRank = rank + 1;
      const previous = ranks.get(targetId);
      if (previous == null || nextRank > previous) {
        ranks.set(targetId, nextRank);
        queue.push(targetId);
      }
    }
  }

  for (const node of nodes) {
    if (!ranks.has(node.id)) {
      ranks.set(node.id, 0);
    }
  }

  return ranks;
}

function computeNodeRanks(nodes: FlowchartNode[], edges: FlowchartV1["edges"]): Map<string, number> {
  const nodeIds = new Set(nodes.map((node) => node.id));
  const validEdges = edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to));
  const backEdgeKeys = findBackEdgeKeys(nodes, validEdges);
  const forwardEdges = validEdges.filter(
    (edge) => !backEdgeKeys.has(`${edge.from}->${edge.to}`)
  );
  return longestPathRanks(nodes, forwardEdges);
}

export function autoLayoutFlowchart(flowchart: FlowchartV1): FlowchartV1 {
  const lanes = normalizeLanes(flowchart.lanes);
  const nodes = assignNodesToLanes({ ...flowchart, lanes }).nodes;
  const ranks = computeNodeRanks(nodes, flowchart.edges);

  if (!lanes.length) {
    return {
      ...flowchart,
      nodes: nodes.map((node, index) => ({
        ...node,
        position: {
          x: 80 + (ranks.get(node.id) ?? 0) * AUTO_LAYOUT_HORIZONTAL_GAP,
          y: 80 + (index % 2) * 96,
        },
      })),
    };
  }

  const groups = new Map<string, FlowchartNode[]>();
  for (const node of nodes) {
    const laneId =
      node.lane_id && lanes.some((lane) => lane.id === node.lane_id)
        ? node.lane_id
        : lanes[0].id;
    const rank = ranks.get(node.id) ?? 0;
    const key = `${laneId}::${rank}`;
    const bucket = groups.get(key) ?? [];
    bucket.push({ ...node, lane_id: laneId });
    groups.set(key, bucket);
  }

  const positions = new Map<string, { x: number; y: number }>();
  for (const lane of lanes) {
    const laneTop = laneTopOffset(lanes, lane.id);
    const laneRankKeys = [...groups.keys()]
      .filter((key) => key.startsWith(`${lane.id}::`))
      .sort((left, right) => {
        const leftRank = Number(left.split("::")[1]);
        const rightRank = Number(right.split("::")[1]);
        return leftRank - rightRank;
      });

    for (const key of laneRankKeys) {
      const bucket = groups.get(key) ?? [];
      bucket.sort((left, right) => left.position.x - right.position.x || left.id.localeCompare(right.id));
      const rank = Number(key.split("::")[1]);
      bucket.forEach((node, stackIndex) => {
        positions.set(node.id, {
          x: AUTO_LAYOUT_START_X + rank * AUTO_LAYOUT_HORIZONTAL_GAP,
          y:
            laneTop +
            LANE_VERTICAL_PADDING +
            stackIndex * (NODE_ESTIMATED_HEIGHT + AUTO_LAYOUT_VERTICAL_GAP),
        });
      });
    }
  }

  const nextNodes = nodes.map((node) => {
    const laneId =
      node.lane_id && lanes.some((lane) => lane.id === node.lane_id)
        ? node.lane_id
        : lanes[0].id;
    return {
      ...node,
      lane_id: laneId,
      position: positions.get(node.id) ?? node.position,
    };
  });

  return fitLaneHeightsToContent({
    ...flowchart,
    lanes,
    nodes: nextNodes,
  });
}
