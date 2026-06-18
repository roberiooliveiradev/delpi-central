import { useEffect, useState } from "react";

import { DELPI_SIDEBAR_EXPAND_EVENT, isPortalSidebarCollapsed } from "../utils/sidebar";

/** Sincroniza com `data-sidebar-collapsed` gravado pela Sidebar. */
export function usePortalSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(() => isPortalSidebarCollapsed());

  useEffect(() => {
    const sync = () => setCollapsed(isPortalSidebarCollapsed());

    sync();

    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-sidebar-collapsed"],
    });

    window.addEventListener(DELPI_SIDEBAR_EXPAND_EVENT, sync);

    return () => {
      observer.disconnect();
      window.removeEventListener(DELPI_SIDEBAR_EXPAND_EVENT, sync);
    };
  }, []);

  return collapsed;
}
