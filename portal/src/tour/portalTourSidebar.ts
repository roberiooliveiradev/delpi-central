export const DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT =
  "DELPI_PORTAL_TOUR_SIDEBAR_PANEL";

export type PortalTourSidebarPanel =
  | "none"
  | "notifications"
  | "theme"
  | "profile";

export function setPortalTourSidebarPanel(panel: PortalTourSidebarPanel) {
  window.dispatchEvent(
    new CustomEvent(DELPI_PORTAL_TOUR_SIDEBAR_PANEL_EVENT, {
      detail: { panel },
    }),
  );
}

export function isPortalTourActive() {
  return document.documentElement.dataset.portalTourActive === "true";
}
