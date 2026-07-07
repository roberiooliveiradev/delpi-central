import { Check, Trash2 } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { FlowchartLane } from "../../types/diagram";
import { FieldLabel } from "@delpi/plugin-ui";
import { SelectControl } from "../ui/SelectControl";
import { mapSelectOptionsFromItems } from "../ui/selectTypes";
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
        <FieldLabel className="tm-field__label" label="Faixa ativa" hint={D.laneSelect} />
        <SelectControl
          ariaLabel="Faixa ativa"
          value={activeLaneId ?? ""}
          onChange={onActiveLaneChange}
          options={mapSelectOptionsFromItems(
            lanes,
            (lane) => lane.id,
            (lane) => lane.label
          )}
        />
      </label>
      <label className="tm-diagram-lane-toolbar__rename">
        <FieldLabel className="tm-field__label" label="Nome da faixa" hint={D.laneRename} />
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
