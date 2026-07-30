import type { LucideIcon } from "lucide-react";

import { HintAction } from "../../help/HintAction";
import { HelpTooltip } from "../../help/HelpTooltip";

type Props = {
  label: string;
  hint: string;
  icon: LucideIcon;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
  variant?: "statusbar" | "floating";
};

export function DiagramEditorActionDockButton({
  label,
  hint,
  icon: Icon,
  onClick,
  disabled = false,
  active = false,
  variant = "statusbar",
}: Props) {
  if (variant === "statusbar") {
    return (
      <HintAction hint={hint} ariaLabel={label}>
        <button
          type="button"
          className={[
            "delpi-ui-bpmn-editor__statusbar-btn",
            active ? "delpi-ui-bpmn-editor__statusbar-btn--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
        >
          <Icon size={14} aria-hidden="true" />
        </button>
      </HintAction>
    );
  }

  return (
    <div className="delpi-ui-bpmn-editor__action-dock-item">
      <span className="delpi-ui-bpmn-editor__action-dock-label">{label}</span>
      <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} wrap placement="top">
        <button
          type="button"
          className={[
            "delpi-ui-bpmn-editor__action-dock-btn",
            active ? "delpi-ui-bpmn-editor__action-dock-btn--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
        >
          <Icon size={18} aria-hidden="true" />
        </button>
      </HelpTooltip>
    </div>
  );
}
