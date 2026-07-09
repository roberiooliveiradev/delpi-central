import { Position } from "@xyflow/react";

export type DiagramNodeBounds = {
  position: { x: number; y: number };
  width?: number;
  height?: number;
};

export const DIAGRAM_NODE_SIZE = {
  box: { width: 168, height: 72 },
  event: { width: 108, height: 64 },
  decision: { width: 108, height: 76 },
} as const;

export function estimateNodeSize(nodeType?: string): { width: number; height: number } {
  if (nodeType === "decision" || nodeType?.startsWith("gateway")) {
    return DIAGRAM_NODE_SIZE.decision;
  }
  if (
    nodeType?.startsWith("start") ||
    nodeType?.startsWith("end") ||
    nodeType?.startsWith("intermediate")
  ) {
    return DIAGRAM_NODE_SIZE.event;
  }
  return DIAGRAM_NODE_SIZE.box;
}

export function nodeCenter(
  node: DiagramNodeBounds,
  fallbackSize = DIAGRAM_NODE_SIZE.box
): { x: number; y: number } {
  const width = node.width ?? fallbackSize.width;
  const height = node.height ?? fallbackSize.height;
  return {
    x: node.position.x + width / 2,
    y: node.position.y + height / 2,
  };
}

export function handleIdsForPositions(
  sourcePosition: Position,
  targetPosition: Position
): { sourceHandle: string; targetHandle: string } {
  const sourceSide = positionToSide(sourcePosition);
  const targetSide = positionToSide(targetPosition);
  return {
    sourceHandle: `${sourceSide}-source`,
    targetHandle: `${targetSide}-target`,
  };
}

function positionToSide(position: Position): "left" | "right" | "top" | "bottom" {
  switch (position) {
    case Position.Left:
      return "left";
    case Position.Right:
      return "right";
    case Position.Top:
      return "top";
    case Position.Bottom:
      return "bottom";
    default:
      return "right";
  }
}

/** Escolhe handles com base na geometria relativa (vertical vs horizontal). */
export function resolveConnectionHandleIds(
  source: DiagramNodeBounds,
  target: DiagramNodeBounds,
  sourceType?: string,
  targetType?: string
): { sourceHandle: string; targetHandle: string } {
  const sourceSize = {
    width: source.width ?? estimateNodeSize(sourceType).width,
    height: source.height ?? estimateNodeSize(sourceType).height,
  };
  const targetSize = {
    width: target.width ?? estimateNodeSize(targetType).width,
    height: target.height ?? estimateNodeSize(targetType).height,
  };

  const sourceCenter = nodeCenter({ ...source, ...sourceSize });
  const targetCenter = nodeCenter({ ...target, ...targetSize });
  const dx = targetCenter.x - sourceCenter.x;
  const dy = targetCenter.y - sourceCenter.y;

  if (Math.abs(dy) > Math.abs(dx) * 0.85) {
    if (dy >= 0) {
      return handleIdsForPositions(Position.Bottom, Position.Top);
    }
    return handleIdsForPositions(Position.Top, Position.Bottom);
  }

  if (dx >= 0) {
    return handleIdsForPositions(Position.Right, Position.Left);
  }
  return handleIdsForPositions(Position.Left, Position.Right);
}
