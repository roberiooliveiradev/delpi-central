import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";

const PANEL_Z_INDEX = 10200;

export type FixedPanelPoint = {
  x: number;
  y: number;
};

export function useFixedPanelPosition(
  open: boolean,
  point: FixedPanelPoint | null,
  panelRef: RefObject<HTMLElement | null>,
  gap = 0,
): CSSProperties {
  const [style, setStyle] = useState<CSSProperties>({
    position: "fixed",
    top: -9999,
    left: -9999,
    zIndex: PANEL_Z_INDEX,
    visibility: "hidden",
  });

  useLayoutEffect(() => {
    if (!open || !point) {
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
      const panel = panelRef.current;
      const panelWidth = panel?.offsetWidth ?? 0;
      const panelHeight = panel?.offsetHeight ?? 0;
      const margin = 8;

      let left = point.x + gap;
      let top = point.y + gap;

      if (panelWidth > 0 && left + panelWidth > window.innerWidth - margin) {
        left = Math.max(margin, window.innerWidth - panelWidth - margin);
      }

      if (panelHeight > 0 && top + panelHeight > window.innerHeight - margin) {
        top = Math.max(margin, window.innerHeight - panelHeight - margin);
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
    resizeObserver?.observe(panel);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("scroll", update);
      resizeObserver?.disconnect();
    };
  }, [gap, open, panelRef, point?.x, point?.y]);

  return style;
}
