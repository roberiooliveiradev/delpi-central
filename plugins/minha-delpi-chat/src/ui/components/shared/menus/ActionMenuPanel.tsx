import type { ReactNode } from "react";

import "../overlay/action-menu.css";

export type ActionMenuItem = {
  id: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
  variant?: "default" | "danger";
  leadingDivider?: boolean;
  onSelect: () => void;
};

type ActionMenuPanelProps = {
  items: ActionMenuItem[];
  onItemSelect?: () => void;
};

export function ActionMenuPanel({ items, onItemSelect }: ActionMenuPanelProps) {
  return (
    <div className="mdc-action-menu__panel">
      {items.map((item) => (
          <div key={item.id}>
            {item.leadingDivider ? (
              <hr className="mdc-action-menu__divider" aria-hidden="true" />
            ) : null}
            <button
              type="button"
              role="menuitem"
              disabled={item.disabled}
              className={[
                "mdc-action-menu__item",
                item.disabled ? "mdc-action-menu__item--disabled" : "",
                item.variant === "danger" ? "mdc-action-menu__item--danger" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={(event) => {
                event.stopPropagation();

                if (item.disabled) {
                  return;
                }

                item.onSelect();
                onItemSelect?.();
              }}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          </div>
        ))}
    </div>
  );
}
