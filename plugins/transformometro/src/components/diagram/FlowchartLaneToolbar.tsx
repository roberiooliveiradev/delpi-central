import { diagramLaneChipToneClass } from "../../utils/diagramLaneColors";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { FlowchartLane } from "../../types/diagram";
import { FieldLabel } from "@delpi/plugin-ui";

const D = TM_HELP_TOOLTIPS.diagramEditor;

type Props = {
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
};

export function FlowchartLaneToolbar({
  lanes,
  activeLaneId,
  onActiveLaneChange,
}: Props) {
  if (!lanes.length) {
    return null;
  }

  return (
    <div className="tm-diagram-lane-toolbar">
      <FieldLabel className="tm-field__label tm-diagram-lane-toolbar__label" label="Faixas" hint={D.laneSelect} />
      <div className="tm-diagram-lane-toolbar__chips" role="listbox" aria-label="Faixas do diagrama">
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
              title={D.laneRename}
            >
              {lane.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
