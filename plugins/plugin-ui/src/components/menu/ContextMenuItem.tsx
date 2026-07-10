import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export type ContextMenuItemProps = {
  label: string;
  icon?: LucideIcon;
  shortcut?: string;
  disabled?: boolean;
  destructive?: boolean;
  onSelect?: () => void;
  children?: ReactNode;
};

export function ContextMenuItem({
  label,
  icon: Icon,
  shortcut,
  disabled = false,
  destructive = false,
  onSelect,
  children,
}: ContextMenuItemProps) {
  return (
    <button
      type="button"
      role="menuitem"
      className={[
        "delpi-ui-context-menu__item",
        destructive ? "delpi-ui-context-menu__item--destructive" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={disabled}
      onClick={() => {
        if (disabled) return;
        onSelect?.();
      }}
    >
      <span className="delpi-ui-context-menu__item-leading" aria-hidden="true">
        {Icon ? <Icon size={16} strokeWidth={1.75} /> : null}
      </span>
      <span className="delpi-ui-context-menu__item-label">{children ?? label}</span>
      {shortcut ? <span className="delpi-ui-context-menu__item-shortcut">{shortcut}</span> : null}
    </button>
  );
}
