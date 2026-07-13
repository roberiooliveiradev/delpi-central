import { useCallback, useState, type PointerEvent as ReactPointerEvent } from "react";

import {
  clampDeckSidePanelWidth,
  getDeckSidePanelLimits,
  readDeckSidePanelCollapsed,
  readDeckSidePanelWidth,
  type DeckSidePanelSide,
  writeDeckSidePanelCollapsed,
  writeDeckSidePanelWidth,
} from "./deckSidePanelLayout";

type Options = {
  /** filmstrip cresce puxando para a direita; inspector (direita) cresce puxando para a esquerda. */
  growDirection: "east" | "west";
};

export function useDeckSidePanelLayout(side: DeckSidePanelSide, options: Options) {
  const limits = getDeckSidePanelLimits(side);
  const [width, setWidthState] = useState(() => readDeckSidePanelWidth(side));
  const [collapsed, setCollapsedState] = useState(() => readDeckSidePanelCollapsed(side));

  const setCollapsed = useCallback(
    (next: boolean) => {
      setCollapsedState(next);
      writeDeckSidePanelCollapsed(side, next);
    },
    [side],
  );

  const toggleCollapsed = useCallback(() => {
    setCollapsedState((current) => {
      const next = !current;
      writeDeckSidePanelCollapsed(side, next);
      return next;
    });
  }, [side]);

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (collapsed) return;
      event.preventDefault();
      event.stopPropagation();

      const startX = event.clientX;
      const startWidth = width;
      let latestWidth = startWidth;
      const sign = options.growDirection === "east" ? 1 : -1;

      const onMove = (moveEvent: PointerEvent) => {
        latestWidth = clampDeckSidePanelWidth(
          side,
          startWidth + sign * (moveEvent.clientX - startX),
        );
        setWidthState(latestWidth);
      };

      const onUp = () => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        writeDeckSidePanelWidth(side, latestWidth);
      };

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    },
    [collapsed, options.growDirection, side, width],
  );

  const panelWidthPx = collapsed ? limits.collapsedWidth : width;

  return {
    width,
    collapsed,
    setCollapsed,
    toggleCollapsed,
    startResize,
    panelWidthPx,
    limits,
  };
}
