import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type ContextMenuItemProps = {
  label: string;
  icon?: LucideIcon;
  shortcut?: string;
  disabled?: boolean;
  destructive?: boolean;
  /** Ajuda in-app no rótulo (hover/foco) — texto canônico do módulo. */
  hint?: string;
  onSelect?: () => void;
  children?: ReactNode;
};

export function ContextMenuItem({
  label,
  icon: Icon,
  shortcut,
  disabled = false,
  destructive = false,
  hint,
  onSelect,
  children,
}: ContextMenuItemProps) {
  const labelContent = children ?? label;

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
      <span className="delpi-ui-context-menu__item-label">
        {hint ? (
          <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} wrap placement="left">
            <span className="delpi-ui-context-menu__item-label-text">{labelContent}</span>
          </HelpTooltip>
        ) : (
          labelContent
        )}
      </span>
      {shortcut ? <span className="delpi-ui-context-menu__item-shortcut">{shortcut}</span> : null}
    </button>
  );
}
