import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type ContextMenuItemProps = {
  label: string;
  icon?: LucideIcon;
  shortcut?: string;
  disabled?: boolean;
  destructive?: boolean;
  /** Ajuda in-app com ícone ? (irmão do menuitem — sem botão aninhado). */
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
    <div className="delpi-ui-context-menu__row" role="none">
      <button
        type="button"
        role="menuitem"
        className={[
          "delpi-ui-context-menu__item",
          destructive ? "delpi-ui-context-menu__item--destructive" : "",
          hint ? "delpi-ui-context-menu__item--with-hint" : "",
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
        <span className="delpi-ui-context-menu__item-label">{labelContent}</span>
        {shortcut ? <span className="delpi-ui-context-menu__item-shortcut">{shortcut}</span> : null}
      </button>
      {hint ? (
        <span className="delpi-ui-context-menu__item-hint" role="none">
          <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} placement="left" />
        </span>
      ) : null}
    </div>
  );
}
