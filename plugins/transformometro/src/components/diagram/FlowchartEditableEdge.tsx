import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeText,
  getSmoothStepPath,
  useReactFlow,
  useStore,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";

import type { FlowchartEdgeKind } from "../../types/diagram";
import {
  adjustEdgeLabelPosition,
  computeEdgePathOffsets,
} from "../../utils/diagramEdgeRouting";
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

function baseEdgeStyle(kind: FlowchartEdgeKind | undefined) {
  const kindStyle = edgeStyle(kind);
  return {
    strokeWidth: 1.5,
    stroke: "var(--tm-diagram-edge-color, #94a3b8)",
    fill: "none",
    ...kindStyle,
  };
}

function resolveSvgLabelText(
  kind: FlowchartEdgeKind,
  displayLabel: string,
  includePlaceholder: boolean
): string | null {
  if (kind === "message_flow") return "Mensagem";
  if (kind === "association") return "Associação";
  if (displayLabel) return displayLabel;
  if (includePlaceholder) return "Rótulo";
  return null;
}

const EDGE_TEXT_LABEL_STYLE = { fill: "var(--ds-text)", fontSize: 11, fontWeight: 600 };
const EDGE_TEXT_BG_STYLE = { fill: "var(--ds-card-bg)", fillOpacity: 0.92 };

export function FlowchartEditableEdge({
  id,
  source,
  target,
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
  const edges = useStore((state) => state.edges);
  const { getNodes } = useReactFlow();
  const pathOffset = computeEdgePathOffsets(edges).get(id) ?? 0;
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 12,
    offset: pathOffset,
  });
  const labelPosition = adjustEdgeLabelPosition(
    { x: labelX, y: labelY },
    {
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourceNodeId: source,
      targetNodeId: target,
    },
    getNodes().filter((node) => node.type !== "lane")
  );

  const displayLabel = typeof label === "string" ? label : "";
  const mergedStyle = { ...style, ...baseEdgeStyle(kind) };
  const showLabelEditor = !edgeData.readOnly && kind === "sequence";
  const svgLabel = resolveSvgLabelText(kind, displayLabel, showLabelEditor);

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={kind === "association" ? undefined : markerEnd}
        style={mergedStyle}
      />
      {svgLabel ? (
        <EdgeText
          x={labelPosition.x}
          y={labelPosition.y}
          label={svgLabel}
          labelStyle={EDGE_TEXT_LABEL_STYLE}
          labelBgStyle={EDGE_TEXT_BG_STYLE}
          labelBgPadding={[2, 6]}
          labelBgBorderRadius={4}
          labelShowBg
          className={
            showLabelEditor
              ? "tm-diagram-edge-label__export-only"
              : "tm-diagram-edge-label__svg"
          }
        />
      ) : null}
      {showLabelEditor ? (
        <EdgeLabelRenderer>
          <div
            className="tm-diagram-edge-label tm-diagram-edge-label--editor nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelPosition.x}px, ${labelPosition.y}px)`,
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
      ) : null}
    </>
  );
}
