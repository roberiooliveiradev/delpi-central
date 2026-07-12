import { createPortal } from "react-dom";
import { type ReactNode, type RefObject } from "react";

import { useAnchoredPanelPosition } from "./useAnchoredPanelPosition";
import { useDelpiUiPortalTheme } from "./useDelpiUiPortalTheme";

export type AnchoredPanelPortalProps = {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  panelRef: RefObject<HTMLDivElement | null>;
  className?: string;
  /** `shape` aplica estilo de menu de forma; `bare` só posiciona o painel. */
  variant?: "shape" | "bare";
  role?: string;
  "aria-label"?: string;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`).
   * Sem escopo, CSS do plugin sob `.dashboard-*` não aplica no body.
   */
  portalScopeClassName?: string;
  children: ReactNode;
};

/** Painel flutuante ancorado ao gatilho via portal no body (evita clip por overflow/z-index). */
export function AnchoredPanelPortal({
  open,
  anchorRef,
  panelRef,
  className,
  variant = "shape",
  role,
  "aria-label": ariaLabel,
  portalScopeClassName,
  children,
}: AnchoredPanelPortalProps) {
  const style = useAnchoredPanelPosition(open, anchorRef, panelRef);
  const theme = useDelpiUiPortalTheme(open, anchorRef);

  if (!open || typeof document === "undefined") return null;

  const panelClass =
    variant === "bare"
      ? className
      : ["delpi-ui-shape-menu__panel", "delpi-ui-shape-menu__panel--portal", className]
          .filter(Boolean)
          .join(" ");

  const scopeClass = [portalScopeClassName, theme.hostClassName].filter(Boolean).join(" ");

  const panel = (
    <div
      ref={panelRef}
      className={panelClass}
      style={style}
      role={role}
      aria-label={ariaLabel}
    >
      {children}
    </div>
  );

  return createPortal(
    <div className={scopeClass} style={theme.style} data-theme={theme.dataTheme}>
      {panel}
    </div>,
    document.body,
  );
}
