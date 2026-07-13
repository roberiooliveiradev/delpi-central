import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type HTMLAttributes,
  type ReactElement,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";
import { resolveMfePortalScopeClassName } from "../shape/delpiUiPortalTheme";
import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";
import {
  resolveKeyTipPosition,
  type KeyTipPlacement,
} from "./keyTipPosition";

export type KeyTipVariant = "shortcut" | "letter";

export type KeyTipProps = {
  /** Texto do balão (ex.: "Ctrl+Z" ou "P"). */
  label: ReactNode;
  /** Quando true, mostra o balão via portal. */
  active: boolean;
  children: ReactElement;
  className?: string;
  /** Preferência; a tela pode inverter se não couber. */
  placement?: KeyTipPlacement;
  /** Desloca o balão horizontalmente (px) para evitar sobreposição. */
  offsetX?: number;
  /**
   * `shortcut` — combinações Ctrl/Del;
   * `letter` — letra única estilo KeyTips Office (F → aba → ação).
   */
  variant?: KeyTipVariant;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`).
   * Se omitido, infere o ancestral `.dashboard-*` do âncora.
   */
  portalScopeClassName?: string;
} & Omit<HTMLAttributes<HTMLSpanElement>, "children" | "className">;

/**
 * Envolve um controle e, com `active`, mostra o atalho em balão (KeyTip)
 * via portal — evita clip por overflow — com flip/clamp na viewport.
 */
export function KeyTip({
  label,
  active,
  children,
  className,
  placement = "top",
  offsetX = 0,
  variant = "shortcut",
  portalScopeClassName,
  ...hostProps
}: KeyTipProps): ReactNode {
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLSpanElement>(null);
  const [style, setStyle] = useState<CSSProperties | null>(null);
  const [resolvedPlacement, setResolvedPlacement] = useState<KeyTipPlacement>(placement);
  const portalTheme = useDelpiUiPortalTheme(active, anchorRef);

  useLayoutEffect(() => {
    if (!active) {
      setStyle(null);
      return;
    }

    const update = () => {
      const anchor = anchorRef.current;
      const tipEl = tipRef.current;
      if (!anchor || !tipEl) return;
      const rect = anchor.getBoundingClientRect();
      const tipWidth = tipEl.offsetWidth || (variant === "letter" ? 28 : 64);
      const tipHeight = tipEl.offsetHeight || 28;
      const next = resolveKeyTipPosition({
        anchor: rect,
        tipWidth,
        tipHeight,
        preferred: placement,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        offsetX,
      });
      setResolvedPlacement(next.placement);
      setStyle({
        position: "fixed",
        top: next.top,
        left: next.left,
        zIndex: DELPI_UI_OVERLAY_Z_INDEX.keyTip,
        transform: "none",
      });
    };

    update();
    const raf = window.requestAnimationFrame(update);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [active, offsetX, placement, variant]);

  const scopeClass = [
    resolveMfePortalScopeClassName(anchorRef.current, portalScopeClassName),
    portalTheme.hostClassName,
  ]
    .filter(Boolean)
    .join(" ");

  const badge = active
    ? createPortal(
        <div
          className={["delpi-ui-keytip-layer", scopeClass].filter(Boolean).join(" ")}
          style={portalTheme.style}
          data-theme={portalTheme.dataTheme}
          aria-hidden="true"
        >
          <span
            ref={tipRef}
            className={[
              "delpi-ui-keytip",
              variant === "letter" ? "delpi-ui-keytip--letter" : "",
              resolvedPlacement === "bottom" ? "delpi-ui-keytip--bottom" : "delpi-ui-keytip--top",
            ]
              .filter(Boolean)
              .join(" ")}
            data-placement={resolvedPlacement}
            style={style ?? { position: "fixed", top: -9999, left: -9999, visibility: "hidden" }}
            role="tooltip"
          >
            {label}
          </span>
        </div>,
        document.body,
      )
    : null;

  return (
    <span
      ref={anchorRef}
      className={["delpi-ui-keytip-anchor", className].filter(Boolean).join(" ")}
      {...hostProps}
    >
      {children}
      {badge}
    </span>
  );
}

export type { KeyTipPlacement };
