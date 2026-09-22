import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import {
  DELPI_HOST_NAVIGATE_EVENT,
  isHostShellPath,
  notifyHostNavigateHandled,
  type HostNavigateDetail,
} from "../utils/hostNavigation";

// Event contract shared with federated MFEs via @delpi/plugin-ui navigateHostPath.

/**
 * Federated MFEs ask the Portal to leave the app shell (e.g. `/profile`)
 * without a full document reload that can land on Home.
 */
export function useHostNavigateListener() {
  const navigate = useNavigate();

  useEffect(() => {
    const onNavigate = (event: Event) => {
      const custom = event as CustomEvent<HostNavigateDetail>;
      const path = (custom.detail?.path || "").trim();
      if (!path.startsWith("/") || path.startsWith("//")) return;

      let pathname = path;
      let search = "";
      let hash = "";
      try {
        const url = new URL(path, window.location.origin);
        pathname = url.pathname;
        search = url.search;
        hash = url.hash;
      } catch {
        return;
      }

      if (!isHostShellPath(pathname)) return;

      notifyHostNavigateHandled();
      navigate(`${pathname}${search}${hash}`);
    };

    window.addEventListener(DELPI_HOST_NAVIGATE_EVENT, onNavigate);
    return () => window.removeEventListener(DELPI_HOST_NAVIGATE_EVENT, onNavigate);
  }, [navigate]);
}
