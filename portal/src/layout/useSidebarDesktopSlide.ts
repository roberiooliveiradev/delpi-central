import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type SetStateAction,
  type TransitionEvent,
} from "react";

import { prefersReducedMotion } from "../tour/portalTourPreferences";
import {
  beginSidebarDesktopCollapse,
  beginSidebarDesktopExpand,
  finishSidebarDesktopEnter,
  finishSidebarDesktopExit,
  isSidebarDesktopSlideTransformEnd,
  markSidebarDesktopExitLeaving,
  PORTAL_SIDEBAR_DESKTOP_SLIDE_FALLBACK_MS,
  resolveSidebarDesktopSlideClassNames,
  shouldRenderSidebarPanelContent,
  shouldShowSidebarEdgeHotspot,
  shouldUseSidebarDesktopSlide,
  type SidebarDesktopSlidePhase,
} from "../utils/sidebarDesktopSlide";

type UseSidebarDesktopSlideOptions = {
  collapsed: boolean;
  setCollapsed: Dispatch<SetStateAction<boolean>>;
  isNarrowViewport: boolean;
  /** Limpeza de UI auxiliar (edge hotspot, timers) antes de expandir. */
  onBeforeExpand?: () => void;
};

function scheduleAfterPaint(callback: () => void): number {
  return window.requestAnimationFrame(() => {
    window.requestAnimationFrame(callback);
  });
}

/**
 * Fluxo canônico do slide desktop da sidebar do portal.
 * Layout (width) muda num salto; o visual anima só com transform.
 */
export function useSidebarDesktopSlide({
  collapsed,
  setCollapsed,
  isNarrowViewport,
  onBeforeExpand,
}: UseSidebarDesktopSlideOptions) {
  const [phase, setPhase] = useState<SidebarDesktopSlidePhase>({
    exit: false,
    exitLeaving: false,
    enter: false,
  });

  const applyState = useCallback(
    (next: {
      collapsed: boolean;
      exit: boolean;
      exitLeaving: boolean;
      enter: boolean;
    }) => {
      setCollapsed(next.collapsed);
      setPhase({
        exit: next.exit,
        exitLeaving: next.exitLeaving,
        enter: next.enter,
      });
    },
    [setCollapsed],
  );

  const collapseSidebar = useCallback(() => {
    const useSlide = shouldUseSidebarDesktopSlide({
      isNarrowViewport,
      prefersReducedMotion: prefersReducedMotion(),
    });
    const current = {
      collapsed,
      exit: phase.exit,
      exitLeaving: phase.exitLeaving,
      enter: phase.enter,
    };
    const next = beginSidebarDesktopCollapse(current, useSlide);
    if (next === current) return;
    applyState(next);
    if (next.exit && !next.exitLeaving) {
      scheduleAfterPaint(() => {
        setPhase((prev) => {
          const marked = markSidebarDesktopExitLeaving({
            collapsed: true,
            ...prev,
          });
          return {
            exit: marked.exit,
            exitLeaving: marked.exitLeaving,
            enter: marked.enter,
          };
        });
      });
    }
  }, [applyState, collapsed, isNarrowViewport, phase]);

  const expandSidebar = useCallback(() => {
    onBeforeExpand?.();
    const useSlide = shouldUseSidebarDesktopSlide({
      isNarrowViewport,
      prefersReducedMotion: prefersReducedMotion(),
    });
    const current = {
      collapsed,
      exit: phase.exit,
      exitLeaving: phase.exitLeaving,
      enter: phase.enter,
    };
    const next = beginSidebarDesktopExpand(current, useSlide);
    applyState(next);
    if (next.enter) {
      scheduleAfterPaint(() => {
        setPhase((prev) => {
          const finished = finishSidebarDesktopEnter({
            collapsed: false,
            ...prev,
          });
          return {
            exit: finished.exit,
            exitLeaving: finished.exitLeaving,
            enter: finished.enter,
          };
        });
      });
    }
  }, [applyState, collapsed, isNarrowViewport, onBeforeExpand, phase]);

  const onSidebarTransitionEnd = useCallback(
    (event: TransitionEvent<HTMLElement>) => {
      if (!isSidebarDesktopSlideTransformEnd(event)) return;
      if (!phase.exit) return;
      setPhase((prev) => {
        const finished = finishSidebarDesktopExit({
          collapsed: true,
          ...prev,
        });
        return {
          exit: finished.exit,
          exitLeaving: finished.exitLeaving,
          enter: finished.enter,
        };
      });
    },
    [phase.exit],
  );

  useEffect(() => {
    if (!phase.exit || !phase.exitLeaving) return;
    const timer = window.setTimeout(() => {
      setPhase((prev) => {
        const finished = finishSidebarDesktopExit({
          collapsed: true,
          ...prev,
        });
        return {
          exit: finished.exit,
          exitLeaving: finished.exitLeaving,
          enter: finished.enter,
        };
      });
    }, PORTAL_SIDEBAR_DESKTOP_SLIDE_FALLBACK_MS);
    return () => window.clearTimeout(timer);
  }, [phase.exit, phase.exitLeaving]);

  const slideClassNames = useMemo(
    () => resolveSidebarDesktopSlideClassNames(phase),
    [phase],
  );

  const showPanelContent = shouldRenderSidebarPanelContent({
    collapsed,
    exit: phase.exit,
  });

  const showEdgeHotspot = shouldShowSidebarEdgeHotspot({
    collapsed,
    exit: phase.exit,
  });

  return {
    collapseSidebar,
    expandSidebar,
    onSidebarTransitionEnd,
    slideClassNames,
    showPanelContent,
    showEdgeHotspot,
    desktopExit: phase.exit,
  };
}
