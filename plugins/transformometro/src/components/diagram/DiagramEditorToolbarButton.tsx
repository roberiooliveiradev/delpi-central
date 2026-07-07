import type { LucideIcon } from "lucide-react";

import { HelpTooltip } from "@delpi/plugin-ui";

type Props = {
  label: string;
  hint: string;
  icon: LucideIcon;
  onClick: () => void;
  disabled?: boolean;
};

export function DiagramEditorToolbarButton({
  label,
  hint,
  icon: Icon,
  onClick,
  disabled = false,
}: Props) {
  return (
    <HelpTooltip
      content={hint}
      ariaLabel={`Ajuda: ${label}`}
      wrap
      placement="bottom"
      className="tm-diagram-editor__tool-wrap"
    >
      <button
        type="button"
        className="ds-ghost-btn tm-diagram-editor__tool-btn"
        onClick={onClick}
        disabled={disabled}
      >
        <Icon size={16} aria-hidden="true" />
        <span>{label}</span>
      </button>
    </HelpTooltip>
  );
}
