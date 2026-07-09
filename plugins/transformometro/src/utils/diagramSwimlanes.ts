import type { FlowchartLane, FlowchartNode, FlowchartV1 } from "../types/diagram";

export const LANE_HEADER_WIDTH = 132;
export const DEFAULT_LANE_HEIGHT = 168;
export const LANE_CANVAS_WIDTH = 2400;
export const AUTO_LAYOUT_HORIZONTAL_GAP = 220;
export const AUTO_LAYOUT_START_X = LANE_HEADER_WIDTH + 48;


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
  laneId?: string
): FlowchartNode {
  if (!lanes.length) {
    return node;
  }
  const targetLaneId = laneId ?? resolveNodeLaneId(node, lanes) ?? lanes[0].id;
  const centerY = laneCenterY(lanes, targetLaneId);
  return {
    ...node,
    lane_id: targetLaneId,
    position: {
      x: Math.max(LANE_HEADER_WIDTH + 24, node.position.x),
      y: centerY - 28,
    },
  };
}

export function defaultNodePosition(
  lanes: FlowchartLane[],
  laneId: string,
  indexInLane = 0
): { x: number; y: number } {
  const centerY = laneCenterY(lanes, laneId);
  return {
    x: LANE_HEADER_WIDTH + 48 + indexInLane * 48,
    y: centerY - 28,
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
  const lanes = normalizeLanes(flowchart.lanes);
  if (!lanes.length) {
    return flowchart;
  }
  return {
    ...flowchart,
    lanes,
    nodes: flowchart.nodes.map((node) => snapNodeToLane(node, lanes, node.lane_id)),
  };
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
    return snapNodeToLane({ ...node, lane_id: fallbackLaneId }, nextLanes, fallbackLaneId);
  });

  return {
    ...flowchart,
    lanes: nextLanes.length ? nextLanes : undefined,
    nodes: nextNodes,
  };
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

function computeNodeRanks(nodes: FlowchartNode[], edges: FlowchartV1["edges"]): Map<string, number> {
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
  const queue = (seeds.length ? seeds : nodes.filter((node) => node.type === "start"))
    .map((node) => node.id);

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

export function autoLayoutFlowchart(flowchart: FlowchartV1): FlowchartV1 {
  const normalized = withNormalizedLanes(flowchart);
  const lanes = normalizeLanes(normalized.lanes);
  const ranks = computeNodeRanks(normalized.nodes, normalized.edges);

  if (!lanes.length) {
    return {
      ...normalized,
      nodes: normalized.nodes.map((node, index) => ({
        ...node,
        position: {
          x: 80 + (ranks.get(node.id) ?? 0) * AUTO_LAYOUT_HORIZONTAL_GAP,
          y: 80 + (index % 2) * 96,
        },
      })),
    };
  }

  const groups = new Map<string, FlowchartNode[]>();
  for (const node of normalized.nodes) {
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
  for (const bucket of groups.values()) {
    bucket.sort((left, right) => left.position.x - right.position.x || left.id.localeCompare(right.id));
    const laneId = bucket[0].lane_id ?? lanes[0].id;
    const rank = ranks.get(bucket[0].id) ?? 0;
    bucket.forEach((node, offsetIndex) => {
      positions.set(node.id, {
        x: AUTO_LAYOUT_START_X + rank * AUTO_LAYOUT_HORIZONTAL_GAP + offsetIndex * 56,
        y: defaultNodePosition(lanes, laneId, 0).y,
      });
    });
  }

  const nextNodes = normalized.nodes.map((node) => {
    const laneId =
      node.lane_id && lanes.some((lane) => lane.id === node.lane_id)
        ? node.lane_id
        : lanes[0].id;
    const position = positions.get(node.id) ?? node.position;
    return snapNodeToLane(
      {
        ...node,
        lane_id: laneId,
        position,
      },
      lanes,
      laneId
    );
  });

  return {
    ...normalized,
    lanes,
    nodes: nextNodes,
  };
}
