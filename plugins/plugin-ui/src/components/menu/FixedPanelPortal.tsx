import { createPortal } from "react-dom";
import {
  useEffect,
  useRef,
  type MouseEvent,
  type ReactNode,
  type RefObject,
} from "react";

import { useClickOutside } from "../shape/useClickOutside";
import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";
import { useFixedPanelPosition, type FixedPanelPoint } from "./useFixedPanelPosition";

export type FixedPanelPortalProps = {
  open: boolean;
  /** Ponto de ancoragem (cursor/rect) — o painel abre a partir daqui. */
  position: FixedPanelPoint | null;
  /** Fecha ao clicar fora ou pressionar Escape. Recomendado em todo popover. */
  onDismiss?: () => void;
  role?: string;
  "aria-label"?: string;
  /** Classe do painel (ex.: `delpi-ui-context-menu`). */
  className?: string;
  /** Folga em px entre o ponto e o painel. */
  gap?: number;
  /** Ref externo ao painel (posicionamento/medida). Default: interno. */
  panelRef?: RefObject<HTMLDivElement | null>;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`).
   * Portais vão para `document.body` — sem este escopo, CSS `--{prefix}-*`
   * e classes de domínio do plugin não aplicam no conteúdo do painel.
   */
  portalScopeClassName?: string;
  onContextMenu?: (event: MouseEvent<HTMLDivElement>) => void;
  children: ReactNode;
};

/**
 * Painel flutuante posicionado por ponto, via portal no body (evita clip por
 * overflow/z-index). Consolida portal + tema + dismiss (clique fora/Escape) +
 * escopo MFE. Consumidores: `ContextMenu` (kit) e popovers de domínio nos MFE.
 * Para ancoragem a um elemento use `AnchoredPanelPortal`.
 */
export function FixedPanelPortal({
  open,
  position,
  onDismiss,
  role,
  "aria-label": ariaLabel,
  className,
  gap = 0,
  panelRef,
  portalScopeClassName,
  onContextMenu,
  children,
}: FixedPanelPortalProps) {
  const internalRef = useRef<HTMLDivElement>(null);
  const resolvedRef = panelRef ?? internalRef;
  const style = useFixedPanelPosition(open, position, resolvedRef, gap);
  const theme = useDelpiUiPortalTheme(open);

  useClickOutside([resolvedRef], Boolean(open && onDismiss), () => {
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

  if (!open || !position || typeof document === "undefined") return null;

  const scopeClass = [portalScopeClassName, theme.hostClassName].filter(Boolean).join(" ");

  return createPortal(
    <div className={scopeClass} style={theme.style} data-theme={theme.dataTheme ?? undefined}>
      <div
        ref={resolvedRef}
        className={className}
        style={style}
        role={role}
        aria-label={ariaLabel}
        onContextMenu={onContextMenu}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
