import type { Node, NodeProps } from "@xyflow/react";

import { GripVertical } from "lucide-react";

import { LANE_HEADER_WIDTH } from "../layout/diagramSwimlanes";
import { DiagramInlineTextEdit } from "../editor/DiagramInlineTextEdit";

type LaneNodeData = {
  label: string;
  height: number;
  laneId?: string;
  toneClass?: string;
  readOnly?: boolean;
  onRename?: (laneId: string, label: string) => void;
  onSelect?: (laneId: string) => void;
};

export function FlowchartLaneNode({ data, selected }: NodeProps<Node<LaneNodeData>>) {
  const canInteract = !data.readOnly && Boolean(data.laneId);

  const selectLane = () => {
    if (canInteract && data.laneId && data.onSelect) {
      data.onSelect(data.laneId);
    }
  };

  return (
    <div
      className={[
        "delpi-ui-bpmn-lane",
        data.toneClass ?? "",
        selected ? "delpi-ui-bpmn-lane--selected" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ width: LANE_HEADER_WIDTH, height: data.height }}
    >
      <div
        className={[
          "delpi-ui-bpmn-lane__header",
          canInteract && data.onRename ? "delpi-ui-bpmn-lane__header--editable" : "",
          canInteract ? "delpi-ui-bpmn-lane__header--selectable" : "",
          canInteract ? "delpi-ui-bpmn-lane__header--draggable" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role={canInteract ? "button" : undefined}
        tabIndex={canInteract ? 0 : undefined}
        aria-pressed={canInteract ? selected : undefined}
        onClick={(event) => {
          if (event.detail > 1) return;
          selectLane();
        }}
        onKeyDown={(event) => {
          if (!canInteract) return;
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectLane();
          }
        }}
      >
        {canInteract ? (
          <span className="delpi-ui-bpmn-lane__drag-handle" aria-hidden>
            <GripVertical size={12} strokeWidth={2.4} />
          </span>
        ) : null}
        <DiagramInlineTextEdit
          value={data.label}
          readOnly={data.readOnly || !data.laneId || !data.onRename}
          onCommit={(next) => {
            if (data.laneId && data.onRename) {
              data.onRename(data.laneId, next);
            }
          }}
          className="delpi-ui-bpmn-lane__label"
          ariaLabel="Nome da faixa"
          emptyFallback="Faixa"
        />
      </div>
    </div>
  );
}
