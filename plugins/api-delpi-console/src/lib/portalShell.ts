export const DELPI_SIDEBAR_EXPAND_EVENT = "DELPI_SIDEBAR_EXPAND";

export function isPortalSidebarCollapsed(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.dataset.sidebarCollapsed === "true";
}

export function expandPortalSidebar(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(DELPI_SIDEBAR_EXPAND_EVENT));
}
