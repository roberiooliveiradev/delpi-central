import { useLayoutEffect, useRef } from "react";

import type { TableRowMenuAction } from "./chatDrillDown";
import { AnchoredMenuPortal } from "./shared/overlay/AnchoredMenuPortal";
import type { ContextMenuAnchor } from "./menuPositionUtils";
import { estimateMenuHeight } from "./menuPositionUtils";
import "./ChatTableRowMenu.css";

export type TableRowMenuAnchor = ContextMenuAnchor;

export function ChatTableRowMenu({
  actions,
  anchor,
  onSelect,
  onClose,
  menuLabel = "Ações da linha",
  scrim = "light",
  variant = "default",
}: {
  actions: TableRowMenuAction[];
  anchor: TableRowMenuAnchor;
  onSelect: (query: string) => void;
  onClose: () => void;
  menuLabel?: string;
  /** `light` = scrim só no painel do chat; `none` = sem scrim. */
  scrim?: "light" | "none";
  /** `actions` = menu «Mais ações» da resposta do assistente. */
  variant?: "default" | "actions";
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!actions.length) {
      return;
    }

    panelRef.current?.focus({ preventScroll: true });
  }, [actions]);

  if (!actions.length) {
    return null;
  }

  return (
    <AnchoredMenuPortal
      open
      anchor={anchor}
      placement="context-menu"
      itemCount={actions.length}
      menuLabel={menuLabel}
      menuRole="menu"
      scrim={scrim === "none" ? "none" : "transparent"}
      shell="overlay"
      panelRef={panelRef}
      panelClassName={[
        "mdc-table-row-menu",
        variant === "actions" ? "mdc-table-row-menu--actions" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClose={onClose}
    >
      {variant === "actions" ? (
        <p className="mdc-table-row-menu__head" aria-hidden="true">
          Mais ações
        </p>
      ) : null}
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          className="mdc-table-row-menu__item"
          role="menuitem"
          onClick={() => {
            onSelect(action.query);
            onClose();
          }}
        >
          {action.label}
        </button>
      ))}
    </AnchoredMenuPortal>
  );
}

export { estimateMenuHeight };
