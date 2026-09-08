/**
 * Slide visual da sidebar desktop sem animar width do flex.
 * Evita React #185 (loop Recharts) ao recolher/expandir.
 */

export const PORTAL_SIDEBAR_DESKTOP_SLIDE_MS = 300;
export const PORTAL_SIDEBAR_DESKTOP_SLIDE_FALLBACK_MS =
  PORTAL_SIDEBAR_DESKTOP_SLIDE_MS + 80;

export const SIDEBAR_DESKTOP_EXIT_CLASS = "is-desktop-exit";
export const SIDEBAR_DESKTOP_EXIT_LEAVING_CLASS = "is-desktop-exit-leaving";
export const SIDEBAR_DESKTOP_ENTER_CLASS = "is-desktop-enter";

export type SidebarDesktopSlidePhase = {
  exit: boolean;
  exitLeaving: boolean;
  enter: boolean;
};

export type SidebarDesktopSlideState = SidebarDesktopSlidePhase & {
  collapsed: boolean;
};

export function shouldUseSidebarDesktopSlide(options: {
  isNarrowViewport: boolean;
  prefersReducedMotion: boolean;
}): boolean {
  return !options.isNarrowViewport && !options.prefersReducedMotion;
}

export function resolveSidebarDesktopSlideClassNames(
  phase: SidebarDesktopSlidePhase,
): string[] {
  const classes: string[] = [];
  if (phase.exit) classes.push(SIDEBAR_DESKTOP_EXIT_CLASS);
  if (phase.exitLeaving) classes.push(SIDEBAR_DESKTOP_EXIT_LEAVING_CLASS);
  if (phase.enter) classes.push(SIDEBAR_DESKTOP_ENTER_CLASS);
  return classes;
}

export function shouldRenderSidebarPanelContent(options: {
  collapsed: boolean;
  exit: boolean;
}): boolean {
  return !options.collapsed || options.exit;
}

export function shouldShowSidebarEdgeHotspot(options: {
  collapsed: boolean;
  exit: boolean;
}): boolean {
  return options.collapsed && !options.exit;
}

export function isSidebarDesktopSlideTransformEnd(event: {
  target: EventTarget | null;
  currentTarget: EventTarget | null;
  propertyName: string;
}): boolean {
  return (
    event.target === event.currentTarget && event.propertyName === "transform"
  );
}

export function beginSidebarDesktopCollapse(
  state: SidebarDesktopSlideState,
  useSlide: boolean,
): SidebarDesktopSlideState {
  if (state.collapsed || state.exit) return state;
  if (!useSlide) {
    return { collapsed: true, exit: false, exitLeaving: false, enter: false };
  }
  return { collapsed: true, exit: true, exitLeaving: false, enter: false };
}

export function markSidebarDesktopExitLeaving(
  state: SidebarDesktopSlideState,
): SidebarDesktopSlideState {
  if (!state.exit) return state;
  return { ...state, exitLeaving: true };
}

export function finishSidebarDesktopExit(
  state: SidebarDesktopSlideState,
): SidebarDesktopSlideState {
  if (!state.exit) return state;
  return { ...state, exit: false, exitLeaving: false };
}

export function beginSidebarDesktopExpand(
  state: SidebarDesktopSlideState,
  useSlide: boolean,
): SidebarDesktopSlideState {
  if (!state.collapsed && !state.exit && !state.enter) {
    return state;
  }
  if (!useSlide) {
    return { collapsed: false, exit: false, exitLeaving: false, enter: false };
  }
  return { collapsed: false, exit: false, exitLeaving: false, enter: true };
}

export function finishSidebarDesktopEnter(
  state: SidebarDesktopSlideState,
): SidebarDesktopSlideState {
  if (!state.enter) return state;
  return { ...state, enter: false };
}
