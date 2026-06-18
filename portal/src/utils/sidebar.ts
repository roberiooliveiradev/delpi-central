/** Evento para reexpandir a sidebar do portal (ex.: MFE detectou menu recolhido). */
export const DELPI_SIDEBAR_EXPAND_EVENT = "DELPI_SIDEBAR_EXPAND";

const SIDEBAR_EDGE_HOTSPOT_SELECTOR = ".sidebar-edge-hotspot";

export const PORTAL_SIDEBAR_EDGE_HOLD_MS = 500;
export const PORTAL_SIDEBAR_EDGE_AUTO_HIDE_MS = 5000;

export function expandPortalSidebar(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(DELPI_SIDEBAR_EXPAND_EVENT));
}

export function isPortalSidebarCollapsed(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.dataset.sidebarCollapsed === "true";
}

/** Largura efetiva da zona de disparo — acompanha o CSS relativo do hotspot. */
export function resolvePortalSidebarEdgeWidth(): number {
  if (typeof document === "undefined") return 20;

  const hotspot = document.querySelector(SIDEBAR_EDGE_HOTSPOT_SELECTOR);
  if (hotspot instanceof HTMLElement) {
    const width = hotspot.getBoundingClientRect().width;
    if (width > 0) return width;
  }

  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue("--portal-sidebar-edge-hotspot-width")
    .trim();
  const parsed = Number.parseFloat(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 20;
}

function readCssLengthPx(value: string, fallback: number): number {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function resolvePortalSidebarEdgeHoldWidth(): number {
  if (typeof document === "undefined") return 20;

  const styles = getComputedStyle(document.documentElement);
  const bandWidth = readCssLengthPx(
    styles.getPropertyValue("--portal-sidebar-edge-band-width"),
    0,
  );

  return Math.max(resolvePortalSidebarEdgeWidth(), bandWidth);
}

/** Faixa esquerda em altura total — equivalente ao hover da borda no desktop. */
export function isPortalSidebarEdgeHoldPoint(clientX: number, _clientY?: number): boolean {
  if (typeof document === "undefined") return false;

  return clientX <= resolvePortalSidebarEdgeHoldWidth();
}
