import { useCallback, useState, type PointerEvent as ReactPointerEvent } from "react";

import {
  clampSidebarWidth,
  readSidebarCollapsed,
  readSidebarWidth,
  SIDEBAR_WIDTH_COLLAPSED,
  writeSidebarCollapsed,
  writeSidebarWidth,
} from "./processoWorkspaceSidebarLayout";

export function useProcessoWorkspaceSidebarLayout() {
  const [width, setWidthState] = useState(readSidebarWidth);
  const [collapsed, setCollapsedState] = useState(readSidebarCollapsed);

  const setCollapsed = useCallback((next: boolean) => {
    setCollapsedState(next);
    writeSidebarCollapsed(next);
  }, []);

  const toggleCollapsed = useCallback(() => {
    setCollapsedState((current) => {
      const next = !current;
      writeSidebarCollapsed(next);
      return next;
    });
  }, []);

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (collapsed) return;
      event.preventDefault();

      const startX = event.clientX;
      const startWidth = width;
      let latestWidth = startWidth;

      const onMove = (moveEvent: PointerEvent) => {
        latestWidth = clampSidebarWidth(startWidth + (moveEvent.clientX - startX));
        setWidthState(latestWidth);
      };

      const onUp = () => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        writeSidebarWidth(latestWidth);
      };

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    },
    [collapsed, width]
  );

  const sidebarWidthPx = collapsed ? SIDEBAR_WIDTH_COLLAPSED : width;

  return {
    width,
    collapsed,
    setCollapsed,
    toggleCollapsed,
    startResize,
    sidebarWidthPx,
  };
}
