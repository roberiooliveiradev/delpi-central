import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";

const PANEL_Z_INDEX = DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel;

export function useAnchoredPanelPosition(
  open: boolean,
  anchorRef: RefObject<HTMLElement | null>,
  panelRef: RefObject<HTMLElement | null>,
  gap = 4,
): CSSProperties {
  const [style, setStyle] = useState<CSSProperties>({
    position: "fixed",
    top: -9999,
    left: -9999,
    zIndex: PANEL_Z_INDEX,
    visibility: "hidden",
  });

  useLayoutEffect(() => {
    if (!open) {
      setStyle({
        position: "fixed",
        top: -9999,
        left: -9999,
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
      const panelWidth = panel?.offsetWidth ?? 0;
      const panelHeight = panel?.offsetHeight ?? 0;
      const margin = 8;

      let left = rect.left;
      let top = rect.bottom + gap;

      if (panelWidth > 0 && left + panelWidth > window.innerWidth - margin) {
        left = Math.max(margin, window.innerWidth - panelWidth - margin);
      }

      if (panelHeight > 0 && top + panelHeight > window.innerHeight - margin) {
        const above = rect.top - panelHeight - gap;
        top = above >= margin ? above : Math.max(margin, window.innerHeight - panelHeight - margin);
      }

      setStyle({
        position: "fixed",
        top,
        left,
        zIndex: PANEL_Z_INDEX,
        visibility: "visible",
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
  }, [anchorRef, gap, open, panelRef]);

  return style;
}
