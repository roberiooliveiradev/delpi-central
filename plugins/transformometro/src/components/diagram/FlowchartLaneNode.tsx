import type { Node, NodeProps } from "@xyflow/react";

import { GripVertical } from "lucide-react";

import { LANE_CANVAS_WIDTH } from "../../utils/diagramSwimlanes";
import { DiagramInlineTextEdit } from "./DiagramInlineTextEdit";

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
        "tm-diagram-lane",
        data.toneClass ?? "",
        selected ? "tm-diagram-lane--selected" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ width: LANE_CANVAS_WIDTH, height: data.height }}
    >
      <div
        className={[
          "tm-diagram-lane__header",
          canInteract && data.onRename ? "tm-diagram-lane__header--editable" : "",
          canInteract ? "tm-diagram-lane__header--selectable" : "",
          canInteract ? "tm-diagram-lane__header--draggable" : "",
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
          <span className="tm-diagram-lane__drag-handle" aria-hidden>
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
          className="tm-diagram-lane__label"
          ariaLabel="Nome da faixa"
          emptyFallback="Faixa"
        />
      </div>
      <div className="tm-diagram-lane__body" />
    </div>
  );
}
