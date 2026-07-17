import type { ReactNode } from "react";

import { FixedPanelPortal } from "./FixedPanelPortal";
import type { FixedPanelPoint } from "./useFixedPanelPosition";

export type ContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
  children: ReactNode;
  "aria-label"?: string;
};

export function ContextMenu({
  open,
  position,
  onClose,
  children,
  "aria-label": ariaLabel,
}: ContextMenuProps) {
  return (
    <FixedPanelPortal
      open={open}
      position={position}
      onDismiss={onClose}
      role="menu"
      aria-label={ariaLabel}
      className="delpi-ui-context-menu"
      onContextMenu={(event) => event.preventDefault()}
    >
      {children}
    </FixedPanelPortal>
  );
}
