import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type ContextMenuItemHintTrigger = "icon" | "label";

export type ContextMenuItemProps = {
  label: string;
  icon?: LucideIcon;
  shortcut?: string;
  disabled?: boolean;
  destructive?: boolean;
  /** Ajuda in-app. */
  hint?: string;
  /**
   * `icon` (default) — botão `?` irmão do menuitem (legado).
   * `label` — help no próprio item, sem coluna de `?`.
   */
  hintTrigger?: ContextMenuItemHintTrigger;
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
  hintTrigger = "icon",
  onSelect,
  children,
}: ContextMenuItemProps) {
  const labelContent = children ?? label;
  const useLabelHint = Boolean(hint) && hintTrigger === "label";
  const useIconHint = Boolean(hint) && hintTrigger === "icon";

  const itemButton = (
    <button
      type="button"
      role="menuitem"
      className={[
        "delpi-ui-context-menu__item",
        destructive ? "delpi-ui-context-menu__item--destructive" : "",
        useIconHint ? "delpi-ui-context-menu__item--with-hint" : "",
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
  );

  return (
    <div
      className={[
        "delpi-ui-context-menu__row",
        useLabelHint ? "delpi-ui-context-menu__row--hint-label" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="none"
    >
      {useLabelHint ? (
        <HelpTooltip content={hint!} ariaLabel={`Ajuda: ${label}`} wrap placement="bottom">
          <span className="delpi-ui-context-menu__item-hit">{itemButton}</span>
        </HelpTooltip>
      ) : (
        itemButton
      )}
      {useIconHint ? (
        <span className="delpi-ui-context-menu__item-hint" role="none">
          <HelpTooltip content={hint!} ariaLabel={`Ajuda: ${label}`} placement="bottom" />
        </span>
      ) : null}
    </div>
  );
}
