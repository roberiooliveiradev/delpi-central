import { useStore, useNodes } from "@xyflow/react";

import {
  LANE_VERTICAL_PADDING,
  NODE_ESTIMATED_HEIGHT,
  requiredSwimlaneCanvasWidth,
} from "../layout/diagramSwimlanes";
import type { BpmnNodeData } from "./FlowchartBpmnNode";

type LaneBackdropData = {
  height?: number;
  toneClass?: string;
  laneId?: string;
};

/** Faixas coloridas atrás das conexões (camada abaixo das edges no viewport). */
export function FlowchartSwimlaneBackdrop() {
  const transform = useStore((state) => state.transform);
  const nodes = useNodes();
  const laneNodes = nodes.filter((node) => node.type === "lane");
  const activityNodes = nodes.filter((node) => node.type !== "lane");
  const [translateX, translateY, zoom] = transform;

  if (!laneNodes.length) {
    return null;
  }

  const canvasWidth = requiredSwimlaneCanvasWidth(
    activityNodes.map((node) => ({
      position: node.position,
      type: (node.data as BpmnNodeData | undefined)?.nodeType,
    }))
  );

  return (
    <div className="delpi-ui-bpmn-swimlane-backdrop" aria-hidden>
      <div
        className="delpi-ui-bpmn-swimlane-backdrop__viewport"
        style={{
          transform: `translate(${translateX}px, ${translateY}px) scale(${zoom})`,
        }}
      >
        {laneNodes.map((lane, index) => {
          const data = lane.data as LaneBackdropData;
          const persistedHeight = data.height ?? 168;
          const nextTop = laneNodes[index + 1]?.position.y;
          let maxBottom = lane.position.y + persistedHeight;
          for (const node of activityNodes) {
            const nodeData = node.data as BpmnNodeData | undefined;
            const belongsById = Boolean(data.laneId) && nodeData?.laneId === data.laneId;
            const belongsByY =
              node.position.y >= lane.position.y &&
              (nextTop == null || node.position.y < nextTop);
            if (!belongsById && !belongsByY) continue;
            maxBottom = Math.max(maxBottom, node.position.y + NODE_ESTIMATED_HEIGHT);
          }
          const height = Math.max(
            persistedHeight,
            maxBottom - lane.position.y + LANE_VERTICAL_PADDING
          );
          return (
            <div
              key={lane.id}
              className={["delpi-ui-bpmn-swimlane-backdrop__band", data.toneClass ?? ""]
                .filter(Boolean)
                .join(" ")}
              style={{
                top: lane.position.y,
                left: 0,
                width: canvasWidth,
                height,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
