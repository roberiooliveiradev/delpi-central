import type { ReactNode } from "react";

import { FixedPanelPortal } from "./FixedPanelPortal";
import type { FixedPanelPoint } from "./useFixedPanelPosition";

export type ContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
  children: ReactNode;
  "aria-label"?: string;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`) — necessária
   * quando o conteúdo do menu usa classes/tokens de domínio do plugin.
   */
  portalScopeClassName?: string;
};

export function ContextMenu({
  open,
  position,
  onClose,
  children,
  "aria-label": ariaLabel,
  portalScopeClassName,
}: ContextMenuProps) {
  return (
    <FixedPanelPortal
      open={open}
      position={position}
      onDismiss={onClose}
      role="menu"
      aria-label={ariaLabel}
      className="delpi-ui-context-menu"
      portalScopeClassName={portalScopeClassName}
      onContextMenu={(event) => event.preventDefault()}
    >
      {children}
    </FixedPanelPortal>
  );
}
