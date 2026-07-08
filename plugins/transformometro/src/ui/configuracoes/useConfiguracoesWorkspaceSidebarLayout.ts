import { useCallback, useState, type PointerEvent as ReactPointerEvent } from "react";

import {
  clampSidebarWidth,
  readConfiguracoesSidebarCollapsed,
  readConfiguracoesSidebarWidth,
  SIDEBAR_WIDTH_COLLAPSED,
  writeConfiguracoesSidebarCollapsed,
  writeConfiguracoesSidebarWidth,
} from "./configuracoesWorkspaceSidebarLayout";

export function useConfiguracoesWorkspaceSidebarLayout() {
  const [width, setWidthState] = useState(readConfiguracoesSidebarWidth);
  const [collapsed, setCollapsedState] = useState(readConfiguracoesSidebarCollapsed);

  const toggleCollapsed = useCallback(() => {
    setCollapsedState((current) => {
      const next = !current;
      writeConfiguracoesSidebarCollapsed(next);
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
        writeConfiguracoesSidebarWidth(latestWidth);
      };

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    },
    [collapsed, width]
  );

  const sidebarWidthPx = collapsed ? SIDEBAR_WIDTH_COLLAPSED : width;

  return { collapsed, toggleCollapsed, startResize, sidebarWidthPx };
}
