import { createPortal } from "react-dom";
import { useEffect, type ReactNode, type RefObject } from "react";

import type { AnchoredPanelPlacement } from "./anchoredPanelCoords";
import { resolveMfePortalScopeClassName } from "./delpiUiPortalTheme";
import { useAnchoredPanelPosition } from "./useAnchoredPanelPosition";
import { useClickOutside } from "./useClickOutside";
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
  /** Larga o painel no mínimo com a largura do gatilho. */
  matchAnchorWidth?: boolean;
  /**
   * Preferência de posição relativa ao âncora.
   * Ex.: `right` = ao lado do botão quando houver espaço.
   */
  preferredPlacement?: AnchoredPanelPlacement;
  /** false = não inverte o lado preferido (ver `resolveAnchoredPanelCoords`). */
  allowFlip?: boolean;
  /** Folga em px entre âncora e painel. */
  gap?: number;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`).
   * Sem escopo, CSS do plugin sob `.dashboard-*` não aplica no body.
   * Se omitido, infere o ancestral `.dashboard-*` do âncora.
   */
  portalScopeClassName?: string;
  /**
   * Fecha o painel ao clicar fora (âncora + painel) ou pressionar Escape.
   * Recomendado em todo popover ancorado.
   */
  onDismiss?: () => void;
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
  matchAnchorWidth = false,
  preferredPlacement = "bottom",
  allowFlip = true,
  gap,
  portalScopeClassName,
  onDismiss,
  children,
}: AnchoredPanelPortalProps) {
  const style = useAnchoredPanelPosition(open, anchorRef, panelRef, {
    matchAnchorWidth,
    preferredPlacement,
    allowFlip,
    ...(gap != null ? { gap } : null),
  });
  const theme = useDelpiUiPortalTheme(open, anchorRef);

  useClickOutside([anchorRef, panelRef], Boolean(open && onDismiss), () => {
    onDismiss?.();
  });

  useEffect(() => {
    const dismiss = onDismiss;
    if (!open || !dismiss) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        dismiss();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onDismiss]);

  if (!open || typeof document === "undefined") return null;

  const panelClass =
    variant === "bare"
      ? className
      : ["delpi-ui-shape-menu__panel", "delpi-ui-shape-menu__panel--portal", className]
          .filter(Boolean)
          .join(" ");

  const scopeClass = [
    resolveMfePortalScopeClassName(anchorRef.current, portalScopeClassName),
    theme.hostClassName,
  ]
    .filter(Boolean)
    .join(" ");

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
