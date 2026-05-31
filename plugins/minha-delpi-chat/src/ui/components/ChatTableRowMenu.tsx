import { useEffect, useRef } from "react";
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

  useEffect(() => {
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

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  if (!actions.length) {
    return null;
  }

  const left = Math.min(anchor.x, window.innerWidth - 240);
  const top = Math.min(anchor.y, window.innerHeight - 280);

  return (
    <div
      ref={panelRef}
      className="mdc-table-row-menu"
      style={{ left, top }}
      role="menu"
      aria-label={menuLabel}
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
  );
}
