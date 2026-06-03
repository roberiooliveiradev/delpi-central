import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { TableRowMenuAction } from "./chatDrillDown";
import {
  isOverlayPortalContained,
  resolveOverlayPortalContainer,
} from "./modalPortalTarget";
import {
  estimateMenuHeight,
  type MenuAnchorRect,
  resolveMenuPosition,
  resolveMenuPositionFromPoint,
  resolveMenuPositionFromPointInContainer,
  resolveMenuPositionInContainer,
} from "./menuPositionUtils";
import "./chat-overlay-layer.css";
import "./ChatTableRowMenu.css";

export type TableRowMenuAnchor =
  | { point: { x: number; y: number } }
  | { rect: MenuAnchorRect };

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
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);

  useLayoutEffect(() => {
    const container = resolveOverlayPortalContainer();
    const containerRect = container.getBoundingClientRect();
    const contained = isOverlayPortalContained(container);

    const nextPosition =
      "rect" in anchor
        ? contained
          ? resolveMenuPositionInContainer({
              rect: anchor.rect,
              containerRect,
              itemCount: actions.length,
            })
          : resolveMenuPosition({ rect: anchor.rect, itemCount: actions.length })
        : contained
          ? resolveMenuPositionFromPointInContainer(
              anchor.point,
              containerRect,
              actions.length,
            )
          : resolveMenuPositionFromPoint(anchor.point, actions.length);

    setPosition(nextPosition);
  }, [actions.length, anchor]);

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

  useLayoutEffect(() => {
    panelRef.current?.focus({ preventScroll: true });
  }, [actions]);

  if (!actions.length || typeof document === "undefined" || !position) {
    return null;
  }

  const menu = (
    <>
      {scrim !== "none" ? (
        <div
          className="mdc-chat-overlay-scrim mdc-table-row-menu__scrim"
          role="presentation"
          aria-hidden="true"
          onMouseDown={onClose}
        />
      ) : null}

      <div
        ref={panelRef}
        className={[
          "mdc-chat-overlay-panel",
          "mdc-chat-overlay-panel--anchored",
          "mdc-table-row-menu",
          variant === "actions" ? "mdc-table-row-menu--actions" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={{ left: position.left, top: position.top }}
        role="menu"
        aria-label={menuLabel}
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
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
      </div>
    </>
  );

  return createPortal(menu, resolveOverlayPortalContainer());
}

export { estimateMenuHeight };
