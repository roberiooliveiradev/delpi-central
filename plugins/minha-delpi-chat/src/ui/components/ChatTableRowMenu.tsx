import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { TableRowMenuAction } from "./chatDrillDown";
import "./ChatTableRowMenu.css";

export function ChatTableRowMenu({
  actions,
  anchor,
  onSelect,
  onClose,
  menuLabel = "Ações da linha",
}: {
  actions: TableRowMenuAction[];
  anchor: { x: number; y: number };
  onSelect: (query: string) => void;
  onClose: () => void;
  menuLabel?: string;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [canUsePortal, setCanUsePortal] = useState(false);

  useEffect(() => {
    setCanUsePortal(true);
  }, []);

  useEffect(() => {
    if (!actions.length) {
      return;
    }

    let cancelled = false;
    let removeListeners: (() => void) | undefined;

    const timeoutId = window.setTimeout(() => {
      if (cancelled) {
        return;
      }

      function handlePointerDown(event: MouseEvent) {
        const target = event.target as Node | null;

        if (panelRef.current && target && !panelRef.current.contains(target)) {
          onClose();
        }
      }

      function handleKeyDown(event: KeyboardEvent) {
        if (event.key === "Escape") {
          onClose();
        }
      }

      document.addEventListener("mousedown", handlePointerDown);
      document.addEventListener("keydown", handleKeyDown);

      removeListeners = () => {
        document.removeEventListener("mousedown", handlePointerDown);
        document.removeEventListener("keydown", handleKeyDown);
      };
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      removeListeners?.();
    };
  }, [actions.length, onClose]);

  if (!actions.length) {
    return null;
  }

  const left = Math.min(anchor.x, window.innerWidth - 240);
  const top = Math.min(anchor.y, window.innerHeight - 280);

  const menu = (
    <>
      <div
        className="mdc-table-row-menu__scrim"
        role="presentation"
        onMouseDown={onClose}
      />

      <div
        ref={panelRef}
        className="mdc-table-row-menu"
        style={{ left, top }}
        role="menu"
        aria-label={menuLabel}
        onMouseDown={(event) => event.stopPropagation()}
      >
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
      </div>
    </>
  );

  if (canUsePortal) {
    return createPortal(menu, document.body);
  }

  return menu;
}
