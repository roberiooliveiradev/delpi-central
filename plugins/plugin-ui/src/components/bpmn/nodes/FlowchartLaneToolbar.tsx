import { diagramLaneChipToneClass } from "../layout/diagramLaneColors";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import type { FlowchartLane } from "../model/diagram";
import { FieldLabel } from "../../help/FieldLabel";

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
    <div className="delpi-ui-bpmn-lane-toolbar">
      <FieldLabel
        className="tm-field__label delpi-ui-bpmn-lane-toolbar__label"
        label={labels.emptyLaneFallback}
        hint={labels.laneSelect}
      />
      <div className="delpi-ui-bpmn-lane-toolbar__chips" role="listbox" aria-label={labels.laneToolbarAriaLabel}>
        {lanes.map((lane, laneIndex) => {
          const isActive = lane.id === activeLaneId;
          return (
            <button
              key={lane.id}
              type="button"
              role="option"
              aria-selected={isActive}
              className={[
                "delpi-ui-bpmn-lane-chip",
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
