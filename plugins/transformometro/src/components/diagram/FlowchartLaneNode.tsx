import type { Node, NodeProps } from "@xyflow/react";

import { LANE_CANVAS_WIDTH } from "../../utils/diagramSwimlanes";
import { DiagramInlineTextEdit } from "./DiagramInlineTextEdit";

type LaneNodeData = {
  label: string;
  height: number;
  laneId?: string;
  readOnly?: boolean;
  onRename?: (laneId: string, label: string) => void;
};

export function FlowchartLaneNode({ data }: NodeProps<Node<LaneNodeData>>) {
  return (
    <div
      className="tm-diagram-lane"
      style={{ width: LANE_CANVAS_WIDTH, height: data.height }}
    >
      <div
        className={[
          "tm-diagram-lane__header",
          !data.readOnly && data.onRename ? "tm-diagram-lane__header--editable" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <DiagramInlineTextEdit
          value={data.label}
          readOnly={data.readOnly || !data.laneId || !data.onRename}
          onCommit={(next) => {
            if (data.laneId && data.onRename) {
              data.onRename(data.laneId, next);
            }
          }}
          className="tm-diagram-lane__label"
          ariaLabel="Nome da faixa"
          emptyFallback="Faixa"
        />
      </div>
      <div className="tm-diagram-lane__body" />
    </div>
  );
}
