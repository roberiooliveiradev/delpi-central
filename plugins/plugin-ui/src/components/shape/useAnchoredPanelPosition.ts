import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";
import {
  resolveAnchoredPanelCoords,
  type AnchoredPanelPlacement,
} from "./anchoredPanelCoords";

const PANEL_Z_INDEX = DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel;

export type AnchoredPanelPositionOptions = {
  gap?: number;
  /** Larga o painel no mínimo com a largura do gatilho (selects). */
  matchAnchorWidth?: boolean;
  /** Preferência de lado; se não couber, tenta alternativas. */
  preferredPlacement?: AnchoredPanelPlacement;
  /** false = não inverte bottom↔top (ribbon). Default true. */
  allowFlip?: boolean;
};

function resolvePositionOptions(
  options: number | AnchoredPanelPositionOptions | undefined,
): Required<AnchoredPanelPositionOptions> {
  if (typeof options === "number") {
    return {
      gap: options,
      matchAnchorWidth: false,
      preferredPlacement: "bottom",
      allowFlip: true,
    };
  }
  return {
    gap: options?.gap ?? 4,
    matchAnchorWidth: Boolean(options?.matchAnchorWidth),
    preferredPlacement: options?.preferredPlacement ?? "bottom",
    allowFlip: options?.allowFlip !== false,
  };
}

export function useAnchoredPanelPosition(
  open: boolean,
  anchorRef: RefObject<HTMLElement | null>,
  panelRef: RefObject<HTMLElement | null>,
  options: number | AnchoredPanelPositionOptions = 4,
): CSSProperties {
  const { gap, matchAnchorWidth, preferredPlacement, allowFlip } = resolvePositionOptions(options);
  const [style, setStyle] = useState<CSSProperties>({
    position: "fixed",
    top: -9999,
    left: -9999,
    right: "auto",
    zIndex: PANEL_Z_INDEX,
    visibility: "hidden",
  });

  useLayoutEffect(() => {
    if (!open) {
      setStyle({
        position: "fixed",
        top: -9999,
        left: -9999,
        right: "auto",
        zIndex: PANEL_Z_INDEX,
        visibility: "hidden",
      });
      return;
    }

    const update = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;

      const rect = anchor.getBoundingClientRect();
      const panel = panelRef.current;
      const panelWidth = Math.max(panel?.offsetWidth ?? 0, matchAnchorWidth ? rect.width : 0);
      const panelHeight = panel?.offsetHeight ?? 0;

      const coords = resolveAnchoredPanelCoords({
        anchor: {
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
          width: rect.width,
          height: rect.height,
        },
        panelWidth,
        panelHeight,
        gap,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        preferredPlacement,
        allowFlip,
      });

      setStyle({
        position: "fixed",
        top: coords.top,
        left: coords.left,
        right: "auto",
        zIndex: PANEL_Z_INDEX,
        visibility: "visible",
        ...(matchAnchorWidth ? { minWidth: rect.width } : null),
      });
    };

    update();
    const raf = requestAnimationFrame(update);

    window.addEventListener("scroll", update, true);
    window.addEventListener("resize", update);
    window.visualViewport?.addEventListener("resize", update);
    window.visualViewport?.addEventListener("scroll", update);

    const panel = panelRef.current;
    const resizeObserver =
      panel && typeof ResizeObserver !== "undefined" ? new ResizeObserver(update) : null;
    if (resizeObserver && panel) resizeObserver.observe(panel);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("scroll", update);
      resizeObserver?.disconnect();
    };
  }, [allowFlip, anchorRef, gap, matchAnchorWidth, open, panelRef, preferredPlacement]);

  return style;
}
