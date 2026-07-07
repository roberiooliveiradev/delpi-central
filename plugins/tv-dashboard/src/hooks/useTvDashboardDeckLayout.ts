import { useEffect } from "react";

const DECK_LAYOUT_CLASS = "tv-dashboard-deck-active";

/** Sinaliza ao portal que o editor deve preencher a área do app (sem scroll duplo). */
export function useTvDashboardDeckLayout(active: boolean): void {
  useEffect(() => {
    if (!active) {
      document.documentElement.classList.remove(DECK_LAYOUT_CLASS);
      return;
    }

    document.documentElement.classList.add(DECK_LAYOUT_CLASS);
    return () => {
      document.documentElement.classList.remove(DECK_LAYOUT_CLASS);
    };
  }, [active]);
}
