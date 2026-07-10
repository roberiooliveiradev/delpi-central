import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export type ContextMenuToolbarButtonProps = {
  label: string;
  icon?: LucideIcon;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  children?: ReactNode;
};

export function ContextMenuToolbarButton({
  label,
  icon: Icon,
  active = false,
  disabled = false,
  onClick,
  children,
}: ContextMenuToolbarButtonProps) {
  return (
    <button
      type="button"
      className={[
        "delpi-ui-context-menu__toolbar-btn",
        active ? "delpi-ui-context-menu__toolbar-btn--active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      title={label}
      aria-label={label}
      disabled={disabled}
      onClick={() => {
        if (disabled) return;
        onClick?.();
      }}
    >
      {children ?? (Icon ? <Icon size={16} strokeWidth={1.75} aria-hidden="true" /> : null)}
    </button>
  );
}
