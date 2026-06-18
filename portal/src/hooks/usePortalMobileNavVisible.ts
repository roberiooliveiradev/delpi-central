import { usePortalMobileChrome } from "./usePortalMobileChrome";
import { resolvePortalMobileNavVisible } from "./portalMobileChromePolicy";
import { usePortalSidebarCollapsed } from "./usePortalSidebarCollapsed";

/** Visibilidade canônica da barra mobile — mutuamente exclusiva com a sidebar aberta. */
export function usePortalMobileNavVisible() {
  const { isNarrowViewport, isLandscapeLayout } = usePortalMobileChrome();
  const sidebarCollapsed = usePortalSidebarCollapsed();

  return {
    showMobileNavBar: resolvePortalMobileNavVisible(
      isNarrowViewport,
      sidebarCollapsed,
    ),
    isLandscapeLayout,
  };
}
