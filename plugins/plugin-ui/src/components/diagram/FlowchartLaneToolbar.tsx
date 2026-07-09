import { diagramLaneChipToneClass } from "./utils/diagramLaneColors";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import type { FlowchartLane } from "./types/diagram";
import { FieldLabel } from "../help/FieldLabel";

type Props = {
  labels: FlowchartEditorLabels;
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
};

export function FlowchartLaneToolbar({
  labels,
  lanes,
  activeLaneId,
  onActiveLaneChange,
}: Props) {
  if (!lanes.length) {
    return null;
  }

  return (
    <div className="tm-diagram-lane-toolbar">
      <FieldLabel
        className="tm-field__label tm-diagram-lane-toolbar__label"
        label={labels.emptyLaneFallback}
        hint={labels.laneSelect}
      />
      <div className="tm-diagram-lane-toolbar__chips" role="listbox" aria-label={labels.laneToolbarAriaLabel}>
        {lanes.map((lane, laneIndex) => {
          const isActive = lane.id === activeLaneId;
          return (
            <button
              key={lane.id}
              type="button"
              role="option"
              aria-selected={isActive}
              className={[
                "tm-diagram-lane-chip",
                diagramLaneChipToneClass(laneIndex),
                isActive ? "is-active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onActiveLaneChange(lane.id)}
              title={labels.laneRename}
            >
              {lane.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
