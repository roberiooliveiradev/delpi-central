import { useEffect } from "react";

const EMBED_LAYOUT_CLASS = "maintenance-embed-active";

export function useMaintenanceEmbedLayout(active: boolean): void {
  useEffect(() => {
    if (!active) return;

    document.documentElement.classList.add(EMBED_LAYOUT_CLASS);
    return () => {
      document.documentElement.classList.remove(EMBED_LAYOUT_CLASS);
    };
  }, [active]);
}
