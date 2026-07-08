export const CONFIGURACOES_WORKSPACE_SIDEBAR_WIDTH_KEY =
  "transformometro.configuracoes.workspaceSidebarWidth";
export const CONFIGURACOES_WORKSPACE_SIDEBAR_COLLAPSED_KEY =
  "transformometro.configuracoes.workspaceSidebarCollapsed";

export const SIDEBAR_WIDTH_MIN = 220;
export const SIDEBAR_WIDTH_MAX = 480;
export const SIDEBAR_WIDTH_DEFAULT = 280;
export const SIDEBAR_WIDTH_COLLAPSED = 52;

export function clampSidebarWidth(value: number): number {
  if (!Number.isFinite(value)) return SIDEBAR_WIDTH_DEFAULT;
  return Math.min(SIDEBAR_WIDTH_MAX, Math.max(SIDEBAR_WIDTH_MIN, Math.round(value)));
}

export function readConfiguracoesSidebarWidth(): number {
  if (typeof window === "undefined") return SIDEBAR_WIDTH_DEFAULT;
  const stored = window.localStorage.getItem(CONFIGURACOES_WORKSPACE_SIDEBAR_WIDTH_KEY);
  if (stored == null) return SIDEBAR_WIDTH_DEFAULT;
  const parsed = Number.parseInt(stored, 10);
  return clampSidebarWidth(parsed);
}

export function writeConfiguracoesSidebarWidth(width: number): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    CONFIGURACOES_WORKSPACE_SIDEBAR_WIDTH_KEY,
    String(clampSidebarWidth(width))
  );
}

export function readConfiguracoesSidebarCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(CONFIGURACOES_WORKSPACE_SIDEBAR_COLLAPSED_KEY) === "1";
}

export function writeConfiguracoesSidebarCollapsed(collapsed: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CONFIGURACOES_WORKSPACE_SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
}
