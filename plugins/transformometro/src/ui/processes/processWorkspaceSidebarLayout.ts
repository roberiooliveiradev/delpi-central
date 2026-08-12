export const PROCESSO_WORKSPACE_SIDEBAR_WIDTH_KEY = "transformometro.processos.workspaceSidebarWidth";
export const PROCESSO_WORKSPACE_SIDEBAR_COLLAPSED_KEY = "transformometro.processos.workspaceSidebarCollapsed";

export const SIDEBAR_WIDTH_MIN = 220;
export const SIDEBAR_WIDTH_MAX = 480;
export const SIDEBAR_WIDTH_DEFAULT = 280;
export const SIDEBAR_WIDTH_COLLAPSED = 52;

export function clampSidebarWidth(value: number): number {
  if (!Number.isFinite(value)) return SIDEBAR_WIDTH_DEFAULT;
  return Math.min(SIDEBAR_WIDTH_MAX, Math.max(SIDEBAR_WIDTH_MIN, Math.round(value)));
}

export function readSidebarWidth(): number {
  if (typeof window === "undefined") return SIDEBAR_WIDTH_DEFAULT;
  const stored = window.localStorage.getItem(PROCESSO_WORKSPACE_SIDEBAR_WIDTH_KEY);
  if (stored == null) return SIDEBAR_WIDTH_DEFAULT;
  const parsed = Number.parseInt(stored, 10);
  return clampSidebarWidth(parsed);
}

export function writeSidebarWidth(width: number): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROCESSO_WORKSPACE_SIDEBAR_WIDTH_KEY, String(clampSidebarWidth(width)));
}

export function readSidebarCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(PROCESSO_WORKSPACE_SIDEBAR_COLLAPSED_KEY) === "1";
}

export function writeSidebarCollapsed(collapsed: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROCESSO_WORKSPACE_SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
}
