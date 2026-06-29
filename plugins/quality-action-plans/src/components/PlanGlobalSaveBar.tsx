import { Save } from "lucide-react";

import {
  PLAN_DIRTY_SECTION_LABELS,
  type PlanDirtySection,
} from "../utils/planDetailDirtyState";

type PlanGlobalSaveBarProps = {
  dirtySections: PlanDirtySection[];
  saving: string | null;
  onSaveAll: () => void;
};

export function PlanGlobalSaveBar({ dirtySections, saving, onSaveAll }: PlanGlobalSaveBarProps) {
  if (!dirtySections.length) {
    return null;
  }

  const busy = saving === "global";

  return (
    <div className="pac-global-save-bar" role="status" aria-live="polite">
      <div className="pac-global-save-bar__summary">
        <strong>
          {dirtySections.length === 1
            ? "1 bloco com alterações não salvas"
            : `${dirtySections.length} blocos com alterações não salvas`}
        </strong>
        <ul className="pac-global-save-bar__list">
          {dirtySections.map((section) => (
            <li key={section}>{PLAN_DIRTY_SECTION_LABELS[section]}</li>
          ))}
        </ul>
      </div>
      <button
        type="button"
        className="pac-primary-btn"
        disabled={Boolean(saving)}
        onClick={onSaveAll}
      >
        <Save size={16} />
        {busy ? "Salvando tudo…" : "Salvar tudo"}
      </button>
    </div>
  );
}
