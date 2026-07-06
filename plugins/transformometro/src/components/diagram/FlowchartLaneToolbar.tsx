import type { FlowchartLane } from "../../types/diagram";

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
        Faixa ativa
        <select value={activeLaneId ?? ""} onChange={(event) => onActiveLaneChange(event.target.value)}>
          {lanes.map((lane) => (
            <option key={lane.id} value={lane.id}>
              {lane.label}
            </option>
          ))}
        </select>
      </label>
      <label className="tm-diagram-lane-toolbar__rename">
        Nome da faixa
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
      <button type="button" className="ds-ghost-btn" onClick={onRenameLane}>
        Aplicar nome
      </button>
      <button
        type="button"
        className="ds-ghost-btn"
        onClick={onRemoveLane}
        disabled={disableRemove}
      >
        Remover faixa
      </button>
    </div>
  );
}
