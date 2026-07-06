import type { Node, NodeProps } from "@xyflow/react";

import { LANE_CANVAS_WIDTH } from "../../utils/diagramSwimlanes";

type LaneNodeData = {
  label: string;
  height: number;
};

export function FlowchartLaneNode({ data }: NodeProps<Node<LaneNodeData>>) {
  return (
    <div
      className="tm-diagram-lane"
      style={{ width: LANE_CANVAS_WIDTH, height: data.height }}
    >
      <div className="tm-diagram-lane__header">
        <span className="tm-diagram-lane__label">{data.label}</span>
      </div>
      <div className="tm-diagram-lane__body" />
    </div>
  );
}
