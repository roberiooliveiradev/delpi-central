import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";

import { DiagramInlineTextEdit } from "./DiagramInlineTextEdit";

export type FlowchartEdgeData = {
  readOnly?: boolean;
  onLabelChange?: (edgeId: string, label: string) => void;
};

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
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  const displayLabel = typeof label === "string" ? label : "";

  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
      {!edgeData.readOnly ? (
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
      ) : displayLabel ? (
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
      ) : null}
    </>
  );
}
