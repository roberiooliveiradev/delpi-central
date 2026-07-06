import { Check, Trash2 } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { FlowchartLane } from "../../types/diagram";
import { FieldLabel } from "../HelpTooltip";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";

const D = TM_HELP_TOOLTIPS.diagramEditor;

type Props = {
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
  laneLabelDraft: string;
  onLaneLabelDraftChange: (value: string) => void;
  onRenameLane: () => void;
  onRemoveLane: () => void;
  disableRemove?: boolean;
};

export function FlowchartLaneToolbar({
  lanes,
  activeLaneId,
  onActiveLaneChange,
  laneLabelDraft,
  onLaneLabelDraftChange,
  onRenameLane,
  onRemoveLane,
  disableRemove = false,
}: Props) {
  if (!lanes.length) {
    return null;
  }

  return (
    <div className="tm-diagram-lane-toolbar">
      <label className="tm-diagram-editor__lane-select">
        <FieldLabel label="Faixa ativa" hint={D.laneSelect} />
        <select value={activeLaneId ?? ""} onChange={(event) => onActiveLaneChange(event.target.value)}>
          {lanes.map((lane) => (
            <option key={lane.id} value={lane.id}>
              {lane.label}
            </option>
          ))}
        </select>
      </label>
      <label className="tm-diagram-lane-toolbar__rename">
        <FieldLabel label="Nome da faixa" hint={D.laneRename} />
        <input
          type="text"
          value={laneLabelDraft}
          onChange={(event) => onLaneLabelDraftChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onRenameLane();
            }
          }}
        />
      </label>
      <DiagramEditorToolbarButton
        label="Aplicar nome"
        hint={D.laneApply}
        icon={Check}
        onClick={onRenameLane}
      />
      <DiagramEditorToolbarButton
        label="Remover faixa"
        hint={D.laneRemove}
        icon={Trash2}
        onClick={onRemoveLane}
        disabled={disableRemove}
      />
    </div>
  );
}
