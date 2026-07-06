import type { FlowchartLane, FlowchartNode, FlowchartV1 } from "../types/diagram";

export const LANE_HEADER_WIDTH = 132;
export const DEFAULT_LANE_HEIGHT = 168;
export const LANE_CANVAS_WIDTH = 2400;


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
