import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";

import type { FlowchartEdgeKind } from "../../types/diagram";
import { DiagramInlineTextEdit } from "./DiagramInlineTextEdit";

export type FlowchartEdgeData = {
  readOnly?: boolean;
  kind?: FlowchartEdgeKind;
  onLabelChange?: (edgeId: string, label: string) => void;
};

function edgeStyle(kind: FlowchartEdgeKind | undefined) {
  if (kind === "message_flow") {
    return {
      strokeDasharray: "6 4",
      stroke: "var(--ds-accent)",
    };
  }
  if (kind === "association") {
    return {
      strokeDasharray: "3 4",
      stroke: "var(--ds-text-muted)",
    };
  }
  return undefined;
}

export function FlowchartEditableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  data,
  markerEnd,
  style,
}: EdgeProps<Edge<FlowchartEdgeData>>) {
  const edgeData = data ?? {};
  const kind = edgeData.kind ?? "sequence";
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  const displayLabel = typeof label === "string" ? label : "";
  const mergedStyle = { ...style, ...edgeStyle(kind) };
  const showLabelEditor = !edgeData.readOnly && kind === "sequence";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={kind === "association" ? undefined : markerEnd}
        style={mergedStyle}
      />
      {showLabelEditor ? (
        <EdgeLabelRenderer>
          <div
            className="tm-diagram-edge-label nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            <DiagramInlineTextEdit
              value={displayLabel}
              readOnly={edgeData.readOnly}
              onCommit={(next) => edgeData.onLabelChange?.(id, next)}
              className="tm-diagram-edge-label__text"
              inputClassName="tm-diagram-edge-label__input"
              ariaLabel="Rótulo da conexão"
              emptyFallback="Rótulo"
              placeholder="Sim / Não"
            />
          </div>
        </EdgeLabelRenderer>
      ) : displayLabel && kind === "sequence" ? (
        <EdgeLabelRenderer>
          <div
            className="tm-diagram-edge-label tm-diagram-edge-label--readonly nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            <span className="tm-diagram-edge-label__text">{displayLabel}</span>
          </div>
        </EdgeLabelRenderer>
      ) : kind !== "sequence" ? (
        <EdgeLabelRenderer>
          <div
            className="tm-diagram-edge-label tm-diagram-edge-label--kind nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            <span className="tm-diagram-edge-label__text">
              {kind === "message_flow" ? "Mensagem" : "Associação"}
            </span>
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
