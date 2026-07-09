import { useStore, useNodes } from "@xyflow/react";

import { LANE_CANVAS_WIDTH, LANE_HEADER_WIDTH } from "../../utils/diagramSwimlanes";

type LaneBackdropData = {
  height?: number;
  toneClass?: string;
};

/** Faixas coloridas atrás das conexões (camada abaixo das edges no viewport). */
export function FlowchartSwimlaneBackdrop() {
  const transform = useStore((state) => state.transform);
  const laneNodes = useNodes().filter((node) => node.type === "lane");
  const [translateX, translateY, zoom] = transform;

  if (!laneNodes.length) {
    return null;
  }

  return (
    <div className="tm-diagram-swimlane-backdrop" aria-hidden>
      <div
        className="tm-diagram-swimlane-backdrop__viewport"
        style={{
          transform: `translate(${translateX}px, ${translateY}px) scale(${zoom})`,
        }}
      >
        {laneNodes.map((lane) => {
          const data = lane.data as LaneBackdropData;
          const height = data.height ?? 168;
          return (
            <div
              key={lane.id}
              className={["tm-diagram-swimlane-backdrop__band", data.toneClass ?? ""]
                .filter(Boolean)
                .join(" ")}
              style={{
                top: lane.position.y,
                left: LANE_HEADER_WIDTH,
                width: LANE_CANVAS_WIDTH - LANE_HEADER_WIDTH,
                height,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
