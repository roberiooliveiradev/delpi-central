import type { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  hint: string;
  icon: LucideIcon;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
};

export function DiagramEditorActionDockButton({
  label,
  hint,
  icon: Icon,
  onClick,
  disabled = false,
  active = false,
}: Props) {
  return (
    <div className="tm-diagram-editor__action-dock-item">
      <span className="tm-diagram-editor__action-dock-label">{label}</span>
      <button
        type="button"
        className={[
          "tm-diagram-editor__action-dock-btn",
          active ? "tm-diagram-editor__action-dock-btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onClick={onClick}
        disabled={disabled}
        aria-label={label}
        title={hint}
      >
        <Icon size={18} aria-hidden="true" />
      </button>
    </div>
  );
}
