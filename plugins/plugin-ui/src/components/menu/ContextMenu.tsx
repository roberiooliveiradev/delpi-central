import { createPortal } from "react-dom";
import { useEffect, useRef, type ReactNode } from "react";

import { useClickOutside } from "../shape/useClickOutside";
import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";
import { useFixedPanelPosition, type FixedPanelPoint } from "./useFixedPanelPosition";

export type ContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
  children: ReactNode;
  "aria-label"?: string;
};

export function ContextMenu({ open, position, onClose, children, "aria-label": ariaLabel }: ContextMenuProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const style = useFixedPanelPosition(open, position, panelRef);
  const theme = useDelpiUiPortalTheme(open);

  useClickOutside([panelRef], open, onClose);

  useEffect(() => {
    if (!open) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  if (!open || !position || typeof document === "undefined") return null;

  return createPortal(
    <div
      ref={panelRef}
      className={[theme.hostClassName, "delpi-ui-context-menu"].filter(Boolean).join(" ")}
      style={{ ...theme.style, ...style }}
      data-theme={theme.dataTheme}
      role="menu"
      aria-label={ariaLabel}
      onContextMenu={(event) => event.preventDefault()}
    >
      {children}
    </div>,
    document.body,
  );
}
