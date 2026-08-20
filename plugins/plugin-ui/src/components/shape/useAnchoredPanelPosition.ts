import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";
import {
  resolveAnchoredPanelCoords,
  type AnchoredPanelPlacement,
} from "./anchoredPanelCoords";

const PANEL_Z_INDEX = DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel;

/** Teto do painel quando cresce além do gatilho (nomes longos em multi-select). */
const MATCH_ANCHOR_MAX_GROW_PX = 480;

export type AnchoredPanelPositionOptions = {
  gap?: number;
  /**
   * Painel no mínimo tão largo quanto o gatilho; pode crescer com o conteúdo
   * até o menor entre viewport e MATCH_ANCHOR_MAX_GROW_PX (não trava max=anchor).
   */
  matchAnchorWidth?: boolean;
  /** Preferência de lado; se não couber, tenta alternativas. */
  preferredPlacement?: AnchoredPanelPlacement;
  /** false = não inverte bottom↔top (ribbon). Default true. */
  allowFlip?: boolean;
  /** Alinhamento horizontal em top/bottom. */
  horizontalAlign?: "start" | "end";
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
      horizontalAlign: "start",
    };
  }
  return {
    gap: options?.gap ?? 4,
    matchAnchorWidth: Boolean(options?.matchAnchorWidth),
    preferredPlacement: options?.preferredPlacement ?? "bottom",
    allowFlip: options?.allowFlip !== false,
    horizontalAlign: options?.horizontalAlign === "end" ? "end" : "start",
  };
}

export function useAnchoredPanelPosition(
  open: boolean,
  anchorRef: RefObject<HTMLElement | null>,
  panelRef: RefObject<HTMLElement | null>,
  options: number | AnchoredPanelPositionOptions = 4,
): CSSProperties {
  const { gap, matchAnchorWidth, preferredPlacement, allowFlip, horizontalAlign } =
    resolvePositionOptions(options);
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
      const viewportMax = Math.max(12 * 16, window.innerWidth - 16);
      const growCap = Math.min(viewportMax, MATCH_ANCHOR_MAX_GROW_PX);
      const panelWidth = Math.max(
        panel?.offsetWidth ?? 0,
        matchAnchorWidth ? rect.width : 0,
      );
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
        panelWidth: matchAnchorWidth
          ? Math.min(growCap, Math.max(panelWidth, rect.width))
          : panelWidth,
        panelHeight,
        gap,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        preferredPlacement,
        allowFlip,
        horizontalAlign,
      });

      setStyle({
        position: "fixed",
        top: coords.top,
        left: coords.left,
        right: "auto",
        zIndex: PANEL_Z_INDEX,
        visibility: "visible",
        ...(matchAnchorWidth
          ? {
              minWidth: rect.width,
              width: "max-content",
              maxWidth: growCap,
            }
          : null),
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
  }, [
    allowFlip,
    anchorRef,
    gap,
    horizontalAlign,
    matchAnchorWidth,
    open,
    panelRef,
    preferredPlacement,
  ]);

  return style;
}
