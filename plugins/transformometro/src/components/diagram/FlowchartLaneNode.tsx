import type { Node, NodeProps } from "@xyflow/react";

import { LANE_CANVAS_WIDTH } from "../../utils/diagramSwimlanes";

type LaneNodeData = {
  label: string;
  height: number;
  laneId?: string;
  readOnly?: boolean;
  onRename?: (laneId: string, label: string) => void;
};

export function FlowchartLaneNode({ data }: NodeProps<Node<LaneNodeData>>) {
  const handleRename = () => {
    if (data.readOnly || !data.laneId || !data.onRename) return;
    const nextLabel = window.prompt("Nome da faixa (swimlane)", data.label);
    if (nextLabel == null) return;
    data.onRename(data.laneId, nextLabel);
  };

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
        onDoubleClick={handleRename}
        title={
          !data.readOnly && data.onRename
            ? "Duplo clique para renomear a faixa"
            : undefined
        }
      >
        <span className="tm-diagram-lane__label">{data.label}</span>
      </div>
      <div className="tm-diagram-lane__body" />
    </div>
  );
}
