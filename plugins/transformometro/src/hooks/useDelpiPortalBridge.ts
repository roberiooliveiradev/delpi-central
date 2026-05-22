import { useEffect } from "react";

import { navigateTransformometro } from "../utils/navigation";
import { normalizeTransformometroPath } from "../utils/routeParser";

/**
 * Integração com o portal (iframe): deep links via DELPI_NAVIGATE
 * e sincronização de URL via DELPI_EMBEDDED_ROUTE.
 */
export function useDelpiPortalBridge(pathname: string) {
  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.data?.type !== "DELPI_NAVIGATE") return;
      const path = event.data?.path;
      if (typeof path !== "string" || !path.trim()) return;
      navigateTransformometro(path);
    }

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || window.parent === window) return;

    const deepPath = normalizeTransformometroPath(pathname);
    window.parent.postMessage({ type: "DELPI_EMBEDDED_ROUTE", path: deepPath }, "*");
  }, [pathname]);
}
