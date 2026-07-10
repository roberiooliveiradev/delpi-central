import { createPortal } from "react-dom";
import { type ReactNode, type RefObject } from "react";

import { useAnchoredPanelPosition } from "./useAnchoredPanelPosition";

export type AnchoredPanelPortalProps = {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  panelRef: RefObject<HTMLDivElement | null>;
  className?: string;
  /** `shape` aplica estilo de menu de forma; `bare` só posiciona o painel. */
  variant?: "shape" | "bare";
  role?: string;
  "aria-label"?: string;
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
  children,
}: AnchoredPanelPortalProps) {
  const style = useAnchoredPanelPosition(open, anchorRef, panelRef);

  if (!open || typeof document === "undefined") return null;

  const panelClass =
    variant === "bare"
      ? className
      : ["delpi-ui-shape-menu__panel", "delpi-ui-shape-menu__panel--portal", className]
          .filter(Boolean)
          .join(" ");

  return createPortal(
    <div ref={panelRef} className={panelClass} style={style} role={role} aria-label={ariaLabel}>
      {children}
    </div>,
    document.body,
  );
}
